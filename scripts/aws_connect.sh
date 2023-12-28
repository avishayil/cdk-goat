#!/bin/bash

CLUSTER_TAG_KEY="App"
CLUSTER_TAG_VALUE="CDKGoat"

# Check if the AWS CLI is installed and configured
if ! aws --version &> /dev/null; then
  echo "AWS CLI is not installed or not configured. Please install and configure it."
  exit 1
fi

# Get the list of cluster ARNs
clusters=$(aws ecs list-clusters --output json | jq -c ".clusterArns[]")

# Flag to check if the cluster with the specified tag is found
clusterFound=false

# Iterate over each cluster ARN
for clusterArn in ${clusters[@]}; do

    # Escape the quotes from clusterArn
    clusterArn=$(echo "$clusterArn" | jq -r)

    # Check if the cluster has the specified tag
    hasTag=0
    hasTag=$(aws ecs list-tags-for-resource --resource-arn "$clusterArn" --output json | jq ".tags | map(select(.key == \"$CLUSTER_TAG_KEY\" and .value == \"$CLUSTER_TAG_VALUE\")) | length")

    if [ $(expr "$hasTag") -gt 0 ]; then
        # Set the flag to true and exit the loop
        clusterFound=true
        break
    fi
done

# If the cluster with the specified tag is found, list tasks in the cluster
if [ "$clusterFound" = true ]; then
    # List tasks in the cluster
    tasks=$(aws ecs list-tasks --cluster "$clusterArn" --output json --query "taskArns")
else
    echo "Cluster with the specified tag not found."
    exit 1
fi

# List the tasks in the specified ECS cluster
tasks_json=$(aws ecs list-tasks --cluster "$clusterArn")
tasks=($(echo "$tasks_json" | jq -r '.taskArns[]'))

# Check if there are any tasks
if [ ${#tasks[@]} -eq 0 ]; then
  echo "No tasks found in the cluster."
  exit 1
fi

echo "Tasks in the $clusterArn cluster:"
for i in "${!tasks[@]}"; do
  echo "$i. ${tasks[i]}"
done

# Ask the user to select a task
read -p "Enter the task number you want to connect to: " taskIndex

# Validate the task index
if ! [[ $taskIndex =~ ^[0-9]+$ ]] || ((taskIndex < 0)) || ((taskIndex >= ${#tasks[@]})); then
  echo "Invalid task selection."
  exit 1
fi

selectedTask=${tasks[taskIndex]}

# List containers in the selected task
containersJson=$(aws ecs describe-tasks --cluster "$clusterArn" --tasks "$selectedTask")
containers=($(echo "$containersJson" | jq -r '.tasks[0].containers[].name'))

echo "Containers in the selected task:"
for i in "${!containers[@]}"; do
  echo "$i. ${containers[i]}"
done

# Ask the user to select a container
read -p "Enter the container number you want to connect to: " containerIndex

# Validate the container index
if ! [[ $containerIndex =~ ^[0-9]+$ ]] || ((containerIndex < 0)) || ((containerIndex >= ${#containers[@]})); then
  echo "Invalid container selection."
  exit 1
fi

selectedContainer=${containers[containerIndex]}

# Execute /bin/bash in the selected container
aws ecs execute-command --cluster "$clusterArn" --task "$selectedTask" --container "$selectedContainer" --interactive --command "/bin/bash"
