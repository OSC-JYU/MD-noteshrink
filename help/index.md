# Noteshrink

Cleans up scans and photos of **notes and documents**. It finds the colour of the paper, keeps
only the colours of the writing, and redraws the page with a handful of colours. Paper texture,
yellowing, bleed-through from the other side and scanner noise disappear, the writing becomes
clearer, and the file becomes much smaller.

It uses [noteshrink](https://github.com/mzucker/noteshrink) by Matt Zucker.

## Task

**Clean up scan** takes a PNG or JPEG image and writes a cleaned PNG image next to it.

Use it before OCR or HTR when backgrounds are uneven, or to make readable copies of notebooks,
whiteboard photos and faded documents. It is not meant for photographs, illustrations or pages
where the paper itself matters (watermarks, paper colour, stains as evidence): those details are
removed on purpose.

## Settings

- **Number of colours** (default 8): colours in the result, the background included. Use 2 for
  plain black-on-white text; keep more when there are several inks, pencil, stamps or coloured
  markings.
- **Background brightness threshold** (default 25 %): how much darker than the paper a pixel must
  be to count as writing. Raise it if paper texture or shadows remain; lower it if faint pencil
  disappears.
- **Background colour threshold** (default 20 %): how much more colourful than the paper a pixel
  must be to count as writing. Raise it if coloured or yellowed paper shows through.
- **White background**: makes the background pure white instead of the paper's own colour.
- **Strengthen colours** (on by default): stretches the colours of the writing to full contrast.
  Turn it off to keep the original tones of the inks.

## Tips

- Compare a couple of settings on one page before running a whole set.
- Crop away dark borders and the neighbouring page first: they are taken for writing.
- The background colour is guessed from the most common colour, so it works best when most of the
  page is paper.

## About noteshrink

[noteshrink](https://github.com/mzucker/noteshrink) by Matt Zucker (MIT licence), explained in his
article [Compressing and enhancing hand-written notes](https://mzucker.github.io/2016/09/20/noteshrink.html).
