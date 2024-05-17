



# MessyDesk wrapper for noteshrink

https://github.com/mzucker/noteshrink

Note: no Dockerfile yet

## API call

curl -X POST -H "Content-Type: multipart/form-data" -F "request=@test/test.json;type=application/json"  -F "content=@test/notesA1.jpg"  http://localhost:5000/process



options


                 num_colors=16,
                 dpi=300,
                 global_palette=False,
                 postprocess_cmd=None,
                 postprocess_ext='.png',
                 quiet=False,
                 saturate=False,
                 basename=None,
                 pdfname=None,
                 pdf_cmd=None):
                 
        self.num_colors = num_colors
        self.dpi = dpi
        self.global_palette = global_palette
        self.postprocess_cmd = postprocess_cmd
        self.postprocess_ext = postprocess_ext
        self.quiet = quiet
        self.saturate = saturate
        self.basename = basename
        self.pdfname = pdfname
        self.pdf_cmd = pdf_cmd