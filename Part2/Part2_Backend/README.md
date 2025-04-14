# Deploy Backend

This guide walks you through deploying and undeploying your Flask backend to **AWS Lambda** using **Zappa**.

---

### 1. navigate into it the project directory that contains the server.py to deploy
- Make sure you have the following files in the directory
    * requirements.text - with the following content:
      - Flask
      - python-dotenv
      - cloudinary
      - flask-cors
      - supabase
      - zappa
### 2. Create and activate a Python virtual environment
- macOS/Linux:
  * python -m venv venv
  * source venv/bin/activate
- Windows(CMD):
  * python -m venv venv
  * venv\Scripts\activate
- Windows(PowerShell):
  * python -m venv venv
  * .\venv\Scripts\Activate.ps1

- After typing in your respective commands you should see a folder named **venv**

### 3. Install dependencies
- pip install -r requirements.txt

### 4. Create a file named zappa_settings.json/Update your zappa_settings.json

### 5. Deploy to AWS
- zappa deploy dev

### 6. Once the Deployment is complete the following services will be created on AWS:
- AWS Lambda Function (runs your Flask app)
- API Gateway (provides the public URL)
- IAM Role (permissions for Lambda to run)
- CloudWatch Logs (captures logs and errors)
- S3 Bucket (used to upload deployment package)


## Undeploy Backend
- zappa undeploy dev
  * This will delete the following resources:
    - Lambda Function
    - API Gateway
    - IAM Role
    - CloudWatch Log Groups
    - Scheduled events (if any)
  * Services that will not get automatically deleted are: S3 Bucket
    - Do delete S3 Bucket:
      * Go to AWS S3 Console
      * Delete the bucket named in zappa_settings.json (if not reused)








