import boto3

ec2_client = boto3.client('ec2', region_name='us-east-2')

def create_ec2_instance():
    try:
        response = ec2_client.run_instances(
            ImageId='ami-0e5497a77ef21b5ac',
            InstanceType='t3.micro',
            MinCount=1,
            MaxCount=1,
        )
        
        # Extract the new Instance ID
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Successfully launched EC2 Instance! ID: {instance_id}")
        return instance_id

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_ec2_instance()
