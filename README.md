
# MessyDesk wrapper for noteshrink

https://github.com/mzucker/noteshrink

Note: no Dockerfile yet

## API call

curl -X POST -H "Content-Type: multipart/form-data" -F "request=@test/test.json;type=application/json"  -F "content=@test/notesA1.jpg"  http://localhost:5000/process

