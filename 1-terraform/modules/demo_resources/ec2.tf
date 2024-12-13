resource "aws_instance" "demo_instance_1" {
    ami           = "ami-0230bd60aa48260c6"
    instance_type = "t3.micro"
    iam_instance_profile = aws_iam_instance_profile.demo_role.id


    tags = {
        Name = "jarvis-demo-approval-needed"
        jarvis-approval-required = "true"
    }
}

resource "aws_instance" "demo_instance_2" {
    ami           = "ami-0230bd60aa48260c6"
    instance_type = "t3.micro"
    iam_instance_profile = aws_iam_instance_profile.demo_role.id


    tags = {
        Name = "jarvis-demo-no-approval"
        jarvis-approval-required = "false"
    }
}

resource "aws_iam_instance_profile" "demo_role" {
  name = "jarvis-demo"
  role = aws_iam_role.demo_2.name
}