# Deploy Frontend to AWS

## 1. Install the adapter
  * npm install -D @sveltejs/adapter-static

## 2. Update svelte.config.js
  * File is uploaded to notion under(important files): **svelte.config.txt**

## 3. Build the App
  * npm run build

## 5. Create and Configure an S3 Bucket
  1. Go to S3 Console
  2. Click "Create bucket"
  3. Choose a unique name like my-sveltekit-app
  4. Choose region (e.g., us-east-1)
  5. Uncheck “Block all public access”
  6. Click Create

## 6. Enable Static Website Hosting
  1. Go to your new bucket
  2. Open the Properties tab
  3. Scroll to “Static website hosting”
  4. Click Edit
  5. Enable it
  6. Set: Index document: **Index.html**; Error document: **Index.html**
  7. Click Save Changes

## 7. Add Bucket Policy for Public Read Access
  1. Go to Permissions tab
  2. Scroll to Bucket policy
  3. Click Edit and paste this (replace your-bucket-name in the file permissions.txt on Notion)
  4. Click Save

## 8. Upload Your App to S3
  1. Go to your bucket → Objects tab
  2. Click Upload
  3. Upload all contents of build/, not the folder itself
  4. Click Upload

## 9. Access Your Live Site
  * S3 Console → Your bucket → Properties → Static website hosting section


