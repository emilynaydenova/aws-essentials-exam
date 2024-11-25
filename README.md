## AWS Essentials October 2024 – Regular Exam
### Assignment
A client wants you to provide a service that processes files. You need to provide them with a simple web interface which has only a button, which chooses a file to upload. This web interface must be accessible from a public IPv4 address.  After uploading this file, a process must be started automatically.
-	The allowed extensions are .pdf, .jpg and .png. In the event of an upload of another file extension (e.g. .txt, .docx, .xlsx), an error notification must be sent to the client. 
-	 The client wants to have file metadata stored in a NoSQL database. For each file upload, they need an entry in the DB with the file size, file extension and date of upload. 
-	When the DB entry is successfully entered, the client needs to receive an E-Mail notification with data about the object (file extension, file size and date of upload).
-	They must be able to retrieve all entries from the DB with a specified file extension within milliseconds. 
-	The files must be stored for 30 minutes, after which they must be deleted automatically. 
The client wants the project in a public GitHub repository, including a CI / CD pipeline that ensures the quality of the code after each push to the master branch.
This repository should include tests for the stack. Add meaningful logs wherever possible to facilitate debugging.

### Solution
 ![Diagram]/assets/images/ExamDiagram.jpg