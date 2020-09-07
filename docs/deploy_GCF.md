# Deply google cloud function from local machine

```
gcloud functions deploy my-python-function --entry-point helloworld --runtime python37 --trigger-http --allow-unauthenticated
```

```
gcloud functions deploy hello_get --entry-point hello_get --runtime python37 --trigger-http --allow-unauthenticated
```