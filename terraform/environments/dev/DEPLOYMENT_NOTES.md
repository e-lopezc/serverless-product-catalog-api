# API Gateway Deployment Notes

### To Deploy:

Use the `-parallelism=1` flag to prevent concurrent modification errors:

```bash
terraform apply -parallelism=1 -var-file=dev.tfvars
```

This tells Terraform to create resources sequentially, avoiding AWS API Gateway's concurrent modification limitations.

### Why This Approach?

- ✅ **Clean code**: No artificial delays or complex dependencies
- ✅ **Faster normal operations**: Only slow down when needed
- ✅ **Reliable**: Guarantees sequential creation
- ✅ **Standard practice**: Uses built-in Terraform feature

### Alternative (if you want parallel by default):

Add to your `dev.tfvars`:
```hcl
# Not a terraform variable, use CLI flag instead
```

Or set environment variable:
```bash
export TF_CLI_ARGS_apply="-parallelism=1"
terraform apply -var-file=dev.tfvars
```
