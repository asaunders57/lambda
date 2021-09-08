# Lambda
Collection of Lambda functions I've created to integrate/glue some services together.

## s3cloudflare
This ensures a S3 bucket serving content fronted by Cloudflare can only be accessed through Cloudflare. 

It assumes that the target S3 bucket policy Statement element contains a statement with the Sid:

`Sid: AllowPublicReadCloudflare`

### Usage
1. Make sure the relevant buckets have a policy that includes a statement with the `Sid` key as mentioned above and an `aws:SourceIp` condition key with an empty list for its value
2. Deploy the Lambda function
3. Create an Eventbridge rule that includes the names of the buckets as input, this works for a single bucket or a list:

```
{
    "bucket_names": "bucket"
}

{
    "bucket_names": [
      "bucket",
      "bucket2",
      "bucket3"
    ]
}
```

## uuid-gen
This is for use with CloudFormation. In Terraform, the same functionality can be provided by the random_uuid resource using the random provider.

The primary use case for this is to ensure that only traffic from CloudFront is permitted when using CloudFront to front an application with an ALB origin.

### Usage
1. Deploy the Lambda function and a custom resource to obtain a uuid, e.g.:

```
Resources:
  InvokeLambdaFunction:
    Type: Custom::UUIDGen
    Version: "1.0"
    Properties:
      ServiceToken: !GetAtt LambdaFunction.Arn

Outputs:
  GeneratedUUID:
    Value: !GetAtt InvokeLambdaFunction.UUID
```
2. Use the output to create a custom origin header with the uuid as its value
3. Add a listener rule to forward requests that contain the custom origin header with the uuid as its value
4. Set the listener default action to return a fixed response of 403
