import pdfkit  # Nécessite wkhtmltopdf installé sur le système
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

def render_maintenance_report_pdf(maintenance, ot, machine, technicien, pieces_utilisees, couts, output_path="maintenance_report.pdf"):
    """
    Génère un PDF du rapport de maintenance à partir du template HTML et des données fournies.
    Args:
        maintenance: objet Maintenance contenant les infos d'intervention
        ot: ordre de travail lié
        machine: objet Machine concerné
        technicien: objet Technicien ayant réalisé l'intervention
        pieces_utilisees: liste des pièces utilisées
        couts: dictionnaire détaillé des coûts (main d'oeuvre, pièces, etc)
        output_path: chemin du fichier PDF à générer
    Returns:
        str: chemin du PDF généré
    """
    env = Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template("maintenance_report_template.html")
    html_content = template.render(
        maintenance=maintenance,
        ot=ot,
        machine=machine,
        technicien=technicien,
        pieces_utilisees=pieces_utilisees,
        couts=couts,
        now=datetime.now()
    )
    # wkhtmltopdf doit être installé et accessible dans le PATH
    pdfkit.from_string(html_content, output_path)
    return output_path
