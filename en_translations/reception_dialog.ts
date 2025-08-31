<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="en">
<context>
<name>ReceptionDialog</name>
<message>
<location filename="../app/ui/dialogs/reception_dialog.py" line="45"/>
<source>Réception Commande ID: %1</source>
<translation>Order Receipt ID: %1</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="63"/>
    <source>Erreur Init</source>
    <translation>Initialization Error</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="63"/>
    <source>Impossible d&apos;initialiser le dialogue de réception:
{e}</source>
    <translation>Unable to initialize the receipt dialog:
{e}</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="92"/>
    <source>Action Impossible</source>
    <translation>Action Not Allowed</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="92"/>
    <source>La commande n&apos;est pas dans un statut permettant la réception ({self.commande.statut}).</source>
    <translation>This order is not in a status that allows receipt ({self.commande.statut}).</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="99"/>
    <source>Info</source>
    <translation>Info</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="99"/>
    <source>Toutes les lignes de cette commande ont déjà été entièrement réceptionnées.</source>
    <translation>All items in this order have already been fully received.</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="106"/>
    <source>Erreur Chargement</source>
    <translation>Loading Error</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="106"/>
    <source>Impossible de charger les données de réception:
{e}</source>
    <translation>Unable to load receipt data:
{e}</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="116"/>
    <source>Commande: %1 - Fournisseur: %2 - Statut: %3</source>
    <translation>Order: %1 - Supplier: %2 - Status: %3</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>ID Ligne</source>
    <translation>Line ID</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>ID Pièce</source>
    <translation>Part ID</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>Réf. Pièce</source>
    <translation>Part Ref.</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>Désignation</source>
    <translation>Description</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>Qté Cmd</source>
    <translation>Ordered Qty</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>Déjà Reçue</source>
    <translation>Already Received</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="120"/>
    <source>Qté Restante</source>
    <translation>Remaining Qty</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="121"/>
    <source>Qté à Réceptionner</source>
    <translation>Qty to Receive</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="133"/>
    <source>Date de Réception:</source>
    <translation>Receipt Date:</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="142"/>
    <source>Enregistrer Réception</source>
    <translation>Save Receipt</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="201"/>
    <source>Date Invalide</source>
    <translation>Invalid Date</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="201"/>
    <source>La date de réception ne peut pas être dans le futur.</source>
    <translation>The receipt date cannot be in the future.</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="218"/>
    <source>Erreur Interne</source>
    <translation>Internal Error</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="218"/>
    <source>Erreur de données pour la ligne {row+1} (Pièce: {nom_piece}).</source>
    <translation>Data error for line {row+1} (Part: {nom_piece}).</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="226"/>
    <source>Quantité Invalide</source>
    <translation>Invalid Quantity</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="226"/>
    <source>Pour la pièce &apos;{nom_piece}&apos;, vous ne pouvez pas réceptionner plus que la quantité restante ({qty_max_recep}).</source>
    <translation>For part '{nom_piece}', you cannot receive more than the remaining quantity ({qty_max_recep}).</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="244"/>
    <source>Aucune Réception</source>
    <translation>No Receipt</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="244"/>
    <source>Aucune quantité n&apos;a été saisie pour la réception.</source>
    <translation>No quantity has been entered for receipt.</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="269"/>
    <source>Pièce &apos;{ligne_info[&apos;nom_piece&apos;]}&apos;: Échec enregistrement (voir logs).</source>
    <translation>Part '{ligne_info['nom_piece']}': Registration failed (see logs).</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="273"/>
    <source>Pièce &apos;{ligne_info[&apos;nom_piece&apos;]}&apos;: {e}</source>
    <translation>Part '{ligne_info['nom_piece']}': {e}</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="276"/>
    <source>Pièce &apos;{ligne_info[&apos;nom_piece&apos;]}&apos;: Erreur serveur.</source>
    <translation>Part '{ligne_info['nom_piece']}': Server error.</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="285"/>
    <source>{success_count} ligne(s) réceptionnée(s) avec succès.

Erreurs survenue(s):
 - {error_details}</source>
    <translation>{success_count} line(s) successfully received.

Errors occurred:
 - {error_details}</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="285"/>
    <source>Réception Partielle / Erreurs</source>
    <translation>Partial Receipt / Errors</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="287"/>
    <source>Succès</source>
    <translation>Success</translation>
</message>
<message>
    <location filename="../app/ui/dialogs/reception_dialog.py" line="287"/>
    <source>{success_count} ligne(s) réceptionnée(s) avec succès.</source>
    <translation>{success_count} line(s) successfully received.</translation>
</message>
</context>
</TS>
