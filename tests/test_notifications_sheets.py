from datetime import date, datetime, timedelta, timezone

import pytest

from reminder_certificati.admin_store import (
    COLONNE_NOTIFICHE,
    ErroreArchivioNotifiche,
    RigaNotifica,
)
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.notifications_sheets import (
    ArchivioNotificheGoogleSheets,
    TrasportoNotificheMemoria,
)
from reminder_certificati.registry import RecordNotifica, StatoNotifica
from reminder_certificati.rules import TIPO_NOTIFICA_SCADENZA

ORA = datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc)
ID_NOTIFICA = f"A-1|2026-08-01|{TIPO_NOTIFICA_SCADENZA}"


def riga_notifica(
    *,
    stato: StatoNotifica = StatoNotifica.SENDING,
    aggiornato_il: datetime = ORA,
    notification_id: str = ID_NOTIFICA,
) -> RigaNotifica:
    arbitro = Arbitro(
        id_arbitro="A-1",
        nome="Anna Maria",
        cognome="Verdi",
        email="anna@example.it",
        scadenza_certificato=date(2026, 8, 1),
    )
    candidato = CandidatoNotifica(
        arbitro=arbitro,
        tipo=TIPO_NOTIFICA_SCADENZA,
        giorni_residui=15,
        notification_id=notification_id,
    )
    record = RecordNotifica(
        notification_id=notification_id,
        stato=stato,
        tentativi=1,
        creato_il=ORA,
        aggiornato_il=aggiornato_il,
        message_id="<test@example.it>" if stato is StatoNotifica.SENT else None,
    )
    return RigaNotifica.da_record(candidato, record, versione_app="0.13.0")


def matrice_con(*righe: RigaNotifica) -> list[list[str]]:
    return [
        list(COLONNE_NOTIFICHE),
        *[
            [riga.come_mappa()[colonna] for colonna in COLONNE_NOTIFICHE]
            for riga in righe
        ],
    ]


def archivio(
    matrice: list[list[str]],
) -> tuple[ArchivioNotificheGoogleSheets, TrasportoNotificheMemoria]:
    trasporto = TrasportoNotificheMemoria(matrice)
    return (
        ArchivioNotificheGoogleSheets(
            trasporto=trasporto,
            spreadsheet_id="spreadsheet-test",
        ),
        trasporto,
    )


def test_chiave_assente_aggiunge_una_sola_riga() -> None:
    matrice = matrice_con()
    adapter, _ = archivio(matrice)
    nuova = riga_notifica()
    adapter.salva(nuova)
    assert len(matrice) == 2
    assert adapter.ottieni(nuova.notification_id) == nuova


def test_chiave_presente_aggiorna_la_stessa_riga() -> None:
    iniziale = riga_notifica()
    matrice = matrice_con(iniziale)
    adapter, _ = archivio(matrice)
    inviata = riga_notifica(
        stato=StatoNotifica.SENT,
        aggiornato_il=ORA + timedelta(minutes=1),
    )
    adapter.salva(inviata)
    assert len(matrice) == 2
    assert adapter.ottieni(inviata.notification_id) == inviata


def test_un_intero_ciclo_usa_una_sola_lettura_del_registro() -> None:
    matrice = matrice_con()
    adapter, trasporto = archivio(matrice)
    sending = riga_notifica()
    sent = riga_notifica(
        stato=StatoNotifica.SENT,
        aggiornato_il=ORA + timedelta(seconds=1),
    )
    assert adapter.ottieni(sending.notification_id) is None
    adapter.salva(sending)
    assert adapter.ottieni(sending.notification_id) == sending
    adapter.salva(sent)
    assert adapter.ottieni(sent.notification_id) == sent
    assert adapter.elenca() == (sent,)
    assert trasporto.letture == 1


def test_ricarica_invalida_la_cache_e_rilegge_il_trasporto() -> None:
    matrice = matrice_con()
    adapter, trasporto = archivio(matrice)

    assert adapter.elenca() == ()
    nuova = riga_notifica()
    matrice.append([nuova.come_mappa()[colonna] for colonna in COLONNE_NOTIFICHE])
    assert adapter.elenca() == ()
    assert adapter.ricarica() == (nuova,)
    assert trasporto.letture == 2


def test_chiave_duplicata_blocca_senza_scrivere() -> None:
    riga = riga_notifica()
    matrice = matrice_con(riga, riga)
    prima = [list(valori) for valori in matrice]
    adapter, _ = archivio(matrice)
    with pytest.raises(ErroreArchivioNotifiche, match="duplicato"):
        adapter.salva(riga)
    assert matrice == prima


def test_intestazioni_diverse_bloccano_la_lettura() -> None:
    matrice = matrice_con()
    matrice[0][0] = "chiave_sbagliata"
    adapter, _ = archivio(matrice)
    with pytest.raises(ErroreArchivioNotifiche, match="intestazioni"):
        adapter.ottieni(ID_NOTIFICA)


def test_rifiuta_regressione_temporale() -> None:
    iniziale = riga_notifica(aggiornato_il=ORA + timedelta(minutes=1))
    matrice = matrice_con(iniziale)
    adapter, _ = archivio(matrice)
    precedente = riga_notifica(aggiornato_il=ORA)
    with pytest.raises(ErroreArchivioNotifiche, match="precedere"):
        adapter.salva(precedente)


def test_nome_scheda_con_apostrofo_viene_escaped() -> None:
    class SpyTrasporto(TrasportoNotificheMemoria):
        ultimo_intervallo: str | None = None

        def leggi_valori(self, *, spreadsheet_id: str, intervallo_a1: str):
            self.ultimo_intervallo = intervallo_a1
            return super().leggi_valori(
                spreadsheet_id=spreadsheet_id,
                intervallo_a1=intervallo_a1,
            )

    trasporto = SpyTrasporto(matrice_con())
    adapter = ArchivioNotificheGoogleSheets(
        trasporto=trasporto,
        spreadsheet_id="spreadsheet-test",
        nome_scheda="NOTIFICHE D'ITALIA",
    )
    adapter.ottieni("inesistente")
    assert trasporto.ultimo_intervallo == "'NOTIFICHE D''ITALIA'!A:K"


def test_configurazione_mancante_non_contatta_il_trasporto() -> None:
    trasporto = TrasportoNotificheMemoria(matrice_con())
    adapter = ArchivioNotificheGoogleSheets(
        trasporto=trasporto,
        spreadsheet_id=" ",
    )
    with pytest.raises(ErroreArchivioNotifiche, match="spreadsheet_id"):
        adapter.ottieni("chiave")
    assert trasporto.letture == 0
