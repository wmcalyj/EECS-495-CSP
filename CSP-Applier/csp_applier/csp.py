class CSP:

    def __init__(self, template):
        self.header = "Content-Security-Policy: script-src 'self' "
        self.sources = template.get_csp_src()

    def generate(self, http_path):
        # JS Part
        for src in self.sources['js']:
            self.header += src + " "
        self.header += http_path + " 'unsafe-eval'; style-src 'self' "

        # CSS Part
        for src in self.sources['css']:
            self.header += src + " "
        self.header += http_path + " 'unsafe-inline'"
