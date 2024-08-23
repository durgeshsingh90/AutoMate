terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.44.0"
    }
  }
}

provider "aws" {
  # Configuration options
}
  resource "aws_instance" "Omnipay" {
  tags = {
    Name = "Omnipay"
  }
  ami           = "ami-0f007bf1d5c770c6e"
  instance_type = "t2.micro"
  key_name      = "Putty"
  security_groups = ["default"]

  user_data = <<-EOF
#!/bin/bash

# Update the system and install necessary packages
sudo yum update -y
sudo yum install -y scp

# Configure SSH for passwordless login
sudo sed -i '/^PasswordAuthentication/s/no/yes/' /etc/ssh/sshd_config
sudo sed -i '/^#PubkeyAuthentication/s/^#//' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Create user f94gdos and set password
sudo useradd f94gdos
echo "password" | sudo passwd --stdin f94gdos
sudo usermod -aG wheel f94gdos

# Add f94gdos to sudoers without password
echo "f94gdos ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers.d/f94gdos_user

# Create bookings.sh script in the home directory of f94gdos
cat << 'BOOKING' > /home/f94gdos/bookings.sh
${file("bookings.sh")}
BOOKING

# Make the bookings.sh script executable
sudo chmod +x /home/f94gdos/bookings.sh

# Ensure the bookings.sh script is owned by the user
sudo chown f94gdos:f94gdos /home/f94gdos/bookings.sh

# Create istparam.cfg file in the home directory of f94gdos
cat << 'ISTPARAM' > /home/f94gdos/istparam.cfg
${file("istparam.cfg")}
ISTPARAM

# Ensure the istparam.cfg file is owned by the user
sudo chown f94gdos:f94gdos /home/f94gdos/istparam.cfg

# Set up SSH authorized_keys for passwordless login
sudo mkdir -p /home/f94gdos/.ssh
cat << 'EOF_KEY' > /home/f94gdos/.ssh/authorized_keys
${file("authorized_keys")}
EOF_KEY

# Set the correct permissions on .ssh directory and authorized_keys file
sudo chmod 700 /home/f94gdos/.ssh
sudo chmod 600 /home/f94gdos/.ssh/authorized_keys

# Ensure the .ssh directory and authorized_keys file are owned by the user
sudo chown -R f94gdos:f94gdos /home/f94gdos/.ssh

EOF
}


output "instance_id" {
  description = "The ID of the Omnipay EC2 instance"
  value       = aws_instance.Omnipay.id
}

output "instance_public_ip" {
  description = "The public IP address of the Omnipay EC2 instance"
  value       = aws_instance.Omnipay.public_ip
}

output "instance_availability_zone" {
  description = "The availability zone of the Omnipay EC2 instance"
  value       = aws_instance.Omnipay.availability_zone
}
