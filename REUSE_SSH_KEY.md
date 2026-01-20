# 🔑 Reusing SSH Key from Accounting Project

This guide shows you how to reuse the same SSH key from your accounting project for the insurance project.

## ✅ **Quick Setup Steps**

### Step 1: Get the Public Key from Your Accounting Server

**Via Termius (connected to your accounting server):**

```bash
# View the authorized_keys file to see the public key
cat ~/.ssh/authorized_keys
```

**Or if you have the key locally:**

**On Windows PowerShell:**
```powershell
# If you saved the key locally for accounting project
Get-Content $env:USERPROFILE\.ssh\vultr_deploy.pub
```

**On Linux/Mac:**
```bash
# If you saved the key locally for accounting project
cat ~/.ssh/vultr_deploy.pub
```

Copy the entire public key (starts with `ssh-rsa` or `ssh-ed25519`)

### Step 2: Add Public Key to Your New Insurance Server

**Via Termius (connected to your new insurance server):**

```bash
# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add the public key to authorized_keys
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys
```

**Replace `YOUR_PUBLIC_KEY_HERE` with the actual public key you copied in Step 1.**

### Step 3: Copy GitHub Secret to Insurance Repository

1. Go to your **accounting project** repository on GitHub
2. Navigate to: **Settings → Secrets and variables → Actions**
3. Find the `VULTR_SSH_KEY` secret
4. Click on it to view (you'll see asterisks, but that's okay)
5. You'll need to get the actual key value from where you originally saved it

**If you have the private key saved locally:**

**On Windows PowerShell:**
```powershell
# On your local machine (PowerShell)
Get-Content $env:USERPROFILE\.ssh\vultr_deploy
```

**On Linux/Mac:**
```bash
# On your local machine
cat ~/.ssh/vultr_deploy
```

Copy the entire private key content (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

### Step 4: Add Secret to Insurance Repository

1. Go to your **insurance project** repository: `batbayarr/insurance`
2. Navigate to: **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"**
4. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `VULTR_HOST` | Your new insurance server IP address |
| `VULTR_USERNAME` | `root` (or your SSH username) |
| `VULTR_SSH_KEY` | The private key content (same as accounting project) |

### Step 5: Test the Connection

**Test SSH connection from your local machine:**

**On Windows PowerShell:**
```powershell
# Replace YOUR_INSURANCE_SERVER_IP with your actual server IP
ssh -i $env:USERPROFILE\.ssh\vultr_deploy root@YOUR_INSURANCE_SERVER_IP
```

**On Linux/Mac:**
```bash
ssh -i ~/.ssh/vultr_deploy root@YOUR_INSURANCE_SERVER_IP
```

**Example (replace with your actual IP):**
```powershell
ssh -i $env:USERPROFILE\.ssh\vultr_deploy root@45.76.123.456
```

If it connects without asking for a password, you're all set!

## 🔍 **Alternative: Copy Key from Accounting Server**

If you need to get the private key from your accounting server (not recommended for security, but possible):

```bash
# On accounting server (via Termius)
cat ~/.ssh/id_rsa
# or
cat ~/.ssh/id_ed25519
```

**Note:** Private keys are usually not stored on servers. You should have it saved locally from when you first set up the accounting project.

## ✅ **Verification**

After setup, test the deployment:

1. Make a small change to your insurance project
2. Push to main branch
3. Check GitHub Actions - it should deploy successfully using the same SSH key

## 🔐 **Security Note**

Using the same SSH key for multiple servers is convenient, but if one server is compromised, both could be at risk. For production, consider using separate keys per project.

---

**Done!** Your insurance project will now use the same SSH key as your accounting project.

