import pdfkit  # Nécessite wkhtmltopdf installé sur le système
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

def render_ot_pdf(ot, machine, technicien, createur, taches, pieces, compteur=None, output_path="ot.pdf"):
    env = Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template("ot_document_template.html")
    html_content = template.render(
        ot=ot,
        machine=machine,
        technicien=technicien,
        createur=createur,
        taches=taches,
        pieces=pieces,
        compteur=compteur,
        now=datetime.now()
    )
    # wkhtmltopdf doit être installé et accessible dans le PATH
    pdfkit.from_string(html_content, output_path)
    return output_path
