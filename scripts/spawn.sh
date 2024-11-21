#!/bin/bash

# Variables
INSTANCE_ID=$1     # Your EC2 instance ID
SEARCH_TAG_KEY=$2  # Tag key used to identify old AMI
SEARCH_TAG_VALUE=$3          # Tag value to identify old AMI
TARGET_GROUP_ARN=$4
if [ "$#" -ne 4 ]; then
echo " Usage : spwan.sh  <INSTANCE_ID> <SEARCH_TAG_KEY> <SEARCH_TAG_VALUE> <TARGET_GROUP_ARN>"
exit 1
fi
# Step 1: Find the old AMI by a specific tag (e.g., backup-new-ami=true)
OLD_AMI_ID=$(aws ec2 describe-images \
    --filters "Name=tag:$SEARCH_TAG_KEY,Values=$SEARCH_TAG_VALUE" \
              "Name=state,Values=available" \
    --query 'Images[0].ImageId' \
    --output text)

if [ "$OLD_AMI_ID" = "None" ]; then
    echo "No existing AMI found with tag: $SEARCH_TAG_KEY=$SEARCH_TAG_VALUE"
    OLD_AMI_ID=""
else
    echo "Found old AMI: $OLD_AMI_ID"
fi

# Step 2: Create a new AMI with a dynamic name (backup-date-time)
NEW_AMI_NAME="backup-$(date +%Y-%m-%d-%H-%M-%S)"
NEW_AMI_ID=$(aws ec2 create-image \
    --instance-id $INSTANCE_ID \
    --name "$NEW_AMI_NAME" \
    --no-reboot \
    --query 'ImageId' \
    --output text)

echo "New AMI created: $NEW_AMI_ID with name: $NEW_AMI_NAME"

# Step 3: Tag the new AMI with the same custom tag (backup-new-ami=true)
aws ec2 create-tags \
    --resources $NEW_AMI_ID \
    --tags Key=$SEARCH_TAG_KEY,Value=$SEARCH_TAG_VALUE
echo "New AMI tagged with $SEARCH_TAG_KEY=$SEARCH_TAG_VALUE"
if [ -n "$OLD_AMI_ID" ]; then
   
    # Step 4: Retrieve the associated snapshots of the old AMI and derefister the Old AMI

    aws ec2 deregister-image --image-id $OLD_AMI_ID
    echo "Ami : $OLD_AMI_ID is deregistered"


else
    echo "No old AMI to delete."
fi

echo "New AMI creation and old AMI cleanup completed."

# Step 5: Retrieve security group and subnet details of the previous instance
SECURITY_GROUPS=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query "Reservations[0].Instances[0].SecurityGroups[*].GroupId" \
    --output text)

SUBNET_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query "Reservations[0].Instances[0].SubnetId" \
    --output text)

echo "Security Groups: $SECURITY_GROUPS"
echo "Subnet ID: $SUBNET_ID"

# Step 6: Launch new instance with the same security group and subnet
echo "Launching new EC2 instance using AMI: $NEW_AMI_ID"
SNAPSHOT_ID=$(aws ec2 describe-images \
    --image-ids $NEW_AMI_ID \
    --query 'Images[0].BlockDeviceMappings[*].Ebs.SnapshotId' \
    --output text)

echo "Waiting for snapshot $SNAPSHOT_ID to complete..."
aws ec2 wait snapshot-completed --snapshot-ids $SNAPSHOT_ID

echo "Snapshot $SNAPSHOT_ID is now completed."


aws ec2 wait image-available --image-ids $NEW_AMI_ID
echo "AMI ami-1234567890abcdef0 is now available."



NEW_INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $NEW_AMI_ID \
    --instance-type t2.micro \
    --security-group-ids $SECURITY_GROUPS \
    --subnet-id $SUBNET_ID \
    --tag-specifications "ResourceType=instance,Tags=[{Key=$SEARCH_TAG_KEY,Value=$SEARCH_TAG_VALUE}]" \
    --query 'Instances[0].InstanceId' \
    --output text)
aws ec2 create-tags  --resources $NEW_INSTANCE_ID --tags Key=Name,Value="backup-ec2"

echo "New instance launched: $NEW_INSTANCE_ID"

aws ec2 wait instance-running --instance-ids $NEW_INSTANCE_ID
echo "Instance $NEW_INSTANCE_ID is now in the running state."


# Step 7: Register the new instance with the target group
aws elbv2 register-targets \
    --target-group-arn $TARGET_GROUP_ARN \
    --targets Id=$NEW_INSTANCE_ID

echo "New instance $NEW_INSTANCE_ID registered with target group $TARGET_GROUP_ARN"
echo "New AMI creation, old AMI cleanup, and instance registration completed."
