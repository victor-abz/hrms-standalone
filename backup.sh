#!/bin/bash

# Cache sudo credentials for the duration of the script
sudo -v

# Check if jq is installed, and if not, install it
if ! command -v jq &> /dev/null; then
    echo "jq is not installed. Installing now..."
    echo $sudo_password | sudo -S apt-get update
    echo $sudo_password | sudo -S apt-get install -y jq
fi

# Set the path to the completed sites file
completed_sites_file="$(pwd)/completed_sites.txt"

# Load completed sites into an array
if [ -f "$completed_sites_file" ]; then
    mapfile -t completed_sites < "$completed_sites_file"
else
    touch "$completed_sites_file"
    completed_sites=()
fi

# Function to check if a site is completed
function is_site_completed() {
    local site_name=$1
    for completed_site in "${completed_sites[@]}"; do
        if [ "$completed_site" == "$site_name" ]; then
            return 0  # Site found in completed list
        fi
    done
    return 1  # Site not found in completed list
}

# Function to add a site to the completed sites file
function add_to_completed_sites() {
    local site_name=$1
    echo "$site_name" >> "$completed_sites_file"
    completed_sites+=("$site_name")
}

# Prompt for the database password
read -s -p "Enter the database password: " db_pwd

# Prompt for the password to use for scp
read -s -p "Enter the password for the destination server: " password

# Prompt for the destination server details
read -p "Enter the username for the destination server: " dest_user
read -p "Enter the IP address of the destination server: " dest_ip
read -p "Enter the path to the destination directory on the server: " dest_path

# Create a parent folder for all backups
backup_parent_folder="full_backups_june_14"
mkdir -p "$backup_parent_folder"

# Loop through all folders in the sites/ directory that match the pattern "*.top1erp.com"
for dir in sites/*.top1erp.com; do

  # Extract the site name from the directory name
  site_name=$(echo "$dir" | sed 's/sites\///' | sed 's/.top1erp.com//')
  full_site_name=$(echo "$dir" | sed 's/sites\///')

  # Check if site is already completed
  if is_site_completed "$site_name"; then
      echo "Skipping $site_name as it is already completed."
      continue
  fi
  # Extract the database name from the site_config.json file
  echo "Setting maintenance mode for $full_site_name"
  bench --site $full_site_name set-maintenance-mode on
  database_name=$(jq -r '.db_name' "$dir/site_config.json")

  # Create a folder for this site's backups
  backup_folder="$backup_parent_folder/$site_name"
  mkdir -p "$backup_folder"

  # Create a backup file name using the current date and time, and the site name
  backup_file="$site_name.sql.gz"

  # Run the MySQL dump command to create a backup of the database
  mysqldump --single-transaction --quick --lock-tables=false -u root -p"$db_pwd" "$database_name" -h 127.0.0.1 -P 3306 --column-statistics=0 | /usr/bin/gzip >> "$backup_folder/$backup_file"
  # Backup the "files" directory inside the "public" directory
  public_files_dir="$dir/public/files"
  if [ -d "$public_files_dir" ]; then
    public_files_backup="public_files.tar.gz"
    tar czf "$backup_folder/$public_files_backup" -C "$public_files_dir" .
  fi

  # Backup the "files" directory inside the "private" directory
  private_files_dir="$dir/private/files"
  if [ -d "$private_files_dir" ]; then
    private_files_backup="private_files.tar.gz"
    tar czf "$backup_folder/$private_files_backup" -C "$private_files_dir" .
  fi
  
  # Backup the quota.json file if it exists
  quota_file="$dir/quota.json"
  if [ -f "$quota_file" ]; then
    cp "$quota_file" "$backup_folder"
  fi

  # Backup the site_config.json file if it exists
  site_config_file="$dir/site_config.json"
  if [ -f "$site_config_file" ]; then
    cp "$site_config_file" "$backup_folder"
  fi

  # Check if the variable equals the specified value
  if [ "$full_site_name" = "hajery.top1erp.com" ]; then
      # Run your command here
      echo "Removing maintenance mode for $full_site_name"
      bench --site $full_site_name set-maintenance-mode off
  fi
  add_to_completed_sites "$site_name"
done

# Zip the backup folder
zip -r "$backup_parent_folder.zip" "$backup_parent_folder"

# Copy the zip file to another server using scp
ssh-keyscan $dest_ip >> ~/.ssh/known_hosts
sshpass -p "$password"  scp "$backup_parent_folder.zip" "$dest_user@$dest_ip:$dest_path"