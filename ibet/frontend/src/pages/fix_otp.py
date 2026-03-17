import re

# Read the file with UTF-8 encoding
with open('StudentDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the pattern
content = re.sub(r'response\.otp_request_id \|\| null', 'response.otp_request_id || response.request_id || null', content)

# Write the file back with UTF-8 encoding
with open('StudentDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully!")
