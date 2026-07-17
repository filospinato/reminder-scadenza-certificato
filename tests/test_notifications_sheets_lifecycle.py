from datetime import date, datetime, timedelta, timezone

from reminder_certificati.admin_store import COLONNE_NOTIFICHE, RigaNotifica
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.notifications_sheets import (
    ArchivioNotificheGoogleSheets,
    TrasportoNotificheMemoria,
)
from reminder_certificati.registry import RecordNotifica, StatoNotifica


ORA = datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc)
CHIAVE = "SYN-1|2026-08-01|REMINDER_30"


def _candidato() -> CandidatoNotifica:
    return CandidatoNotifica(
        arbitro=Arbitro(
            id_arbitro="SYN-1",
            nome="Anna Maria",
            cognome="Verdi",
            email="synthetic@example.invalid",
            scadenza_certificato=date(2026, 8, 1),
        ),
        tipo="REMINDER_30",
        giorni_residui=15,
        notification_id=CHIAVE,
    )


def _riga(
    stato: StatoNotifica,
    *,
    tentativi: int = 1,
    aggiornato_il: datetime = ORA,
    message_id: str | None = None,
    errore: str | None = None,
) -> RigaNotifica:
    return RigaNotifica.da_record(
        _candidato(),
        RecordNotifica(
            notification_id=CHIAVE,
            stato=stato,
            tentativi=tentativi,
            creato_il=ORA,
            aggiornato_il=aggiornato_il,
            message_id=message_id,
            errore=errore,
        ),
        versione_app="test-sintetico",
    )


def _nuovo_adapter(matrice: list[list[str]]) -> ArchivioNotificheGoogleSheets:
    return ArchivioNotificheGoogleSheets(
        trasporto=TrasportoNotificheMemoria(matrice),
        spreadsheet_id="spreadsheet-sintetico",
    )


def test_ciclo_persistente_resiste_a_rerun_e_aggiorna_una_sola_riga() -> None:
    matrice: list[list[str]] = [list(COLONNE_NOTIFICHE)]

    prima_esecuzione = _nuovo_adapter(matrice)
    prenotata = _riga(StatoNotifica.SENDING)
    prima_esecuzione.salva(prenotata)

    # Simula un crash dopo la prenotazione e un nuovo processo che rilegge Sheets.
    seconda_esecuzione = _nuovo_adapter(matrice)
    riletta = seconda_esecuzione.ottieni(CHIAVE)
    assert riletta is not None
    assert riletta.stato is StatoNotifica.SENDING
    assert len(matrice) == 2

    inviata = _riga(
        StatoNotifica.SENT,
        aggiornato_il=ORA + timedelta(minutes=1),
        message_id="<synthetic@example.invalid>",
    )
    seconda_esecuzione.salva(inviata)

    terza_esecuzione = _nuovo_adapter(matrice)
    finale = terza_esecuzione.ottieni(CHIAVE)
    assert finale is not None
    assert finale.stato is StatoNotifica.SENT
    assert finale.message_id == "<synthetic@example.invalid>"
    assert finale.tentativi == 1
    assert len(matrice) == 2


def test_retry_aggiorna_la_stessa_riga_e_incrementa_i_tentativi() -> None:
    matrice: list[list[str]] = [list(COLONNE_NOTIFICHE)]
    adapter = _nuovo_adapter(matrice)
    adapter.salva(_riga(StatoNotifica.SENDING))
    adapter.salva(
        _riga(
            StatoNotifica.FAILED_RETRYABLE,
            aggiornato_il=ORA + timedelta(minutes=1),
            errore="errore sintetico ritentabile",
        )
    )

    nuovo_processo = _nuovo_adapter(matrice)
    nuovo_processo.salva(
        _riga(
            StatoNotifica.SENDING,
            tentativi=2,
            aggiornato_il=ORA + timedelta(minutes=2),
        )
    )

    riletta = _nuovo_adapter(matrice).ottieni(CHIAVE)
    assert riletta is not None
    assert riletta.stato is StatoNotifica.SENDING
    assert riletta.tentativi == 2
    assert riletta.errore is None
    assert len(matrice) == 2
