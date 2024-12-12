#!/usr/bin/env python
from cdktf import App
from stack import Stack

app = App()
Stack(app, "ToriSearchAiStack")
app.synth()
