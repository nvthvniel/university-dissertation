# Default vpc ID
data "aws_vpc" "default" {}

data "aws_region" "current" {}

data "aws_subnets" "filter" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name = "availability-zone"
    values = ["${data.aws_region.current.name}a", "${data.aws_region.current.name}b", "${data.aws_region.current.name}c"]
  }
}

data "aws_subnet" "subnets" {
  for_each = toset(data.aws_subnets.filter.ids)
  id       = each.value
}