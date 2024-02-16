## Testing of 2 pdf to text methods:
There are two pdf methods that I found that work pretty well.
These are **pypdf** and **PyMuPDF** or 'fitz' as it prefers to be imported.
Both are successful at pulling out text that is clearly in resolution and that you would normally interpret as *important*.
From what it looks like, the only major difference is that pypdf is more likely to put text that is clearly on the same line in the source
on two different lines in its interpretation.
Of note is the fact that PuMuPDF is *much* faster

Pros: Easy and simple to use, also relatively fast all things considered

Cons: Picks up extra garbage characters that aren't text.
These include things like formatting lines to make the text easier to read which it records as | or -.
It also can't recognize very small or ambiguous characters which we might be able to fix with upscaling in images.

Tried: https://github.com/pymupdf/PyMuPDF and https://github.com/py-pdf/pypdf

## Testing of 1 pdf to image to text methods

I just tried tesseract as the pdf to image to text method. It did noticeably worse than both pdf methods.
It ignored spaces often and does bad with numbers in certain places but not others.
The one place it is useful though is that there are certain documents that cannot be processed with the pdf to text methods and it can do that.
Maybe I need to try a different way of doing things, but right now the pdf to text methods are the way to go.

Pros: Works on any document and if someone had only image data, then it would be easy to input.
It also recognizes some smaller characters that the other methods didn't recognize

Cons: Harder to set up and image processing takes much longer. Ignores characters more often than the other methods.
Picks up formatting lines that make the text easier to read.

Tried: https://github.com/madmaze/pytesseract