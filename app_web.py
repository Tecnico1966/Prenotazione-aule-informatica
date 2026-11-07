import streamlit as st
import sqlite3
import os
from datetime import datetime

# Configurazione della pagina
st.set_page_config(page_title="Prenotazione Laboratori e Aule", page_icon="🏫", layout="wide")

# Firma di Copyright
st.sidebar.markdown("### © Rosario Abate")
st.sidebar.info("Sistema di Gestione e Prenotazione Laboratori e Aule Scolastiche.")

# --- INIZIALIZZAZIONE DATABASE ---
def init_db():
    cartella_utente = os.path.expanduser("~")
    db_path = os.path.join(cartella_utente, "laboratori.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabella Prenotazioni
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prenotazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            progetto TEXT,
            professore TEXT NOT NULL,
            materia TEXT NOT NULL,
            tutor TEXT,
            esperto TEXT,
            tecnico TEXT,
            num_alunni INTEGER,
            aula TEXT NOT NULL,
            data TEXT NOT NULL,
            ora_inizio TEXT NOT NULL,
            ora_fine TEXT NOT NULL,
            note TEXT,
            UNIQUE(aula, data, ora_inizio)
        )
    ''')

    # Tabella Aule Dinamica
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()

    # Inserisce aule predefinite se vuota
    cursor.execute("SELECT COUNT(*) FROM aule")
    if cursor.fetchone()[0] == 0:
        aule_default = [
            ("Lab. Informatica 1",), 
            ("Lab. Informatica 2",), 
            ("Lab. Multimediale",), 
            ("Aula Magna",)
        ]
        cursor.executemany("INSERT INTO aule (nome) VALUES (?)", aule_default)
        conn.commit()
    
    return conn, cursor

conn, cursor = init_db()

def get_lista_aule():
    cursor.execute("SELECT nome FROM aule ORDER BY nome ASC")
    return [row[0] for row in cursor.fetchall()]

# --- INTERFACCIA WEB ---
st.title("🏫 Prenotazione Laboratori e Aule scolastiche")

tab1, tab2, tab3 = st.tabs(["📅 Calendario e Prenotazioni", "➕ Nuova Prenotazione", "⚙️ Gestione Aule"])

# --- TAB 1: CALENDARIO E FILTRI ---
with tab1:
    st.subheader("Elenco Prenotazioni Attive")
    
    col_f1, col_f2 = st.columns(2)
    lista_aule = get_lista_aule()
    filtro_aula = col_f1.selectbox("Filtra per Laboratorio", ["Tutti"] + lista_aule)
    filtro_data = col_f2.text_input("Filtra per Data (AAAA-MM-GG, lascia vuoto per tutti)", "")

    query = "SELECT id, progetto, professore, materia, tutor, esperto, tecnico, num_alunni, aula, data, ora_inizio, ora_fine FROM prenotazioni WHERE 1=1"
    parametri = []

    if filtro_aula != "Tutti":
        query += " AND aula = ?"
        parametri.append(filtro_aula)

    if filtro_data.strip():
        query += " AND data = ?"
        parametri.append(filtro_data.strip())

    query += " ORDER BY data DESC, ora_inizio ASC"
    
    cursor.execute(query, parametri)
    righe = cursor.fetchall()

    if righe:
        # Mostra tabella pulita
        dati_tabella = []
        for r in righe:
            dati_tabella.append({
                "ID": r[0],
                "Progetto": r[1],
                "Docente": r[2],
                "Materia": r[3],
                "Tutor": r[4],
                "Esperto": r[5],
                "Tecnico": r[6],
                "N° Alunni": r[7],
                "Aula": r[8],
                "Data": r[9],
                "Inizio": r[10],
                "Fine": r[11]
            })
        st.dataframe(dati_tabella, use_container_width=True)
    else:
        st.info("Nessuna prenotazione trovata con i filtri selezionati.")

    # Sezione Cancellazione
    st.markdown("---")
    st.subheader("Cancella una Prenotazione")
    id_da_cancellare = st.number_input("Inserisci l'ID della prenotazione da eliminare", min_value=1, step=1)
    if st.button("Elimina Prenotazione Selezionata"):
        cursor.execute("DELETE FROM prenotazioni WHERE id = ?", (id_da_cancellare,))
        conn.commit()
        st.success(f"Prenotazione ID {id_da_cancellare} eliminata con successo!")
        st.rerun()

# --- TAB 2: NUOVA PRENOTAZIONE ---
with tab2:
    st.subheader("Inserisci una Nuova Prenotazione")
    
    with st.form("form_prenotazione"):
        col1, col2 = st.columns(2)
        
        with col1:
            progetto = st.text_input("Nome Progetto")
            professore = st.text_input("Docente / Richiedente *")
            materia = st.text_input("Materia / Classe *")
            tutor = st.text_input("Tutor")
            
        with col2:
            esperto = st.text_input("Esperto")
            tecnico = st.text_input("Tecnico Presente")
            num_alunni = st.number_input("Numero Alunni", min_value=1, max_value=150, value=20)
            aula_scelta = st.selectbox("Laboratorio / Aula *", get_lista_aule())

        col3, col4, col5 = st.columns(3)
        with col3:
            data_prenotazione = st.text_input("Data (AAAA-MM-GG)", value=datetime.today().strftime('%Y-%m-%d'))
        with col4:
            orari_disponibili = [
                "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", 
                "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"
            ]
            ora_inizio = st.selectbox("Ora Inizio", orari_disponibili, index=0)
        with col5:
            ora_fine = st.selectbox("Ora Fine", orari_disponibili, index=1)

        submitted = st.form_submit_button("Registra Prenotazione")

        if submitted:
            if not professore.strip() or not materia.strip() or not data_prenotazione.strip():
                st.error("Compilare tutti i campi obbligatori contrassegnati con l'asterisco (*).")
            elif ora_inizio >= ora_fine:
                st.error("L'ora di inizio deve essere precedente all'ora di fine.")
            else:
                try:
                    datetime.strptime(data_prenotazione, '%Y-%m-%d')
                except ValueError:
                    st.error("Formato data non valido. Usare AAAA-MM-GG.")
                    st.stop()

                # Controllo sovrapposizioni
                cursor.execute('''
                    SELECT * FROM prenotazioni 
                    WHERE aula = ? AND data = ? 
                    AND (ora_inizio < ? AND ora_fine > ?)
                ''', (aula_scelta, data_prenotazione, ora_fine, ora_inizio))

                if cursor.fetchone():
                    st.error(f"Conflitto: L'aula '{aula_scelta}' è già occupata il {data_prenotazione} nella fascia oraria richiesta!")
                else:
                    try:
                        cursor.execute('''
                            INSERT INTO prenotazioni (progetto, professore, materia, tutor, esperto, tecnico, num_alunni, aula, data, ora_inizio, ora_fine)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (progetto, professore, materia, tutor, esperto, tecnico, num_alunni, aula_scelta, data_prenotazione, ora_inizio, ora_fine))
                        conn.commit()
                        st.success("Prenotazione registrata con successo!")
                    except Exception as e:
                        st.error(f"Errore durante il salvataggio: {e}")

# --- TAB 3: GESTIONE AULE ---
with tab3:
    st.subheader("Aggiungi o Rimuovi Aule / Laboratori")
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        st.markdown("### Aule Attuali")
        for a in get_lista_aule():
            st.text(f"• {a}")
            
    with col_a2:
        st.markdown("### Nuova Aula")
        nuova_aula = st.text_input("Nome della nuova aula/laboratorio")
        if st.button("Aggiungi Aula"):
            if nuova_aula.strip():
                try:
                    cursor.execute("INSERT INTO aule (nome) VALUES (?)", (nuova_aula.strip(),))
                    conn.commit()
                    st.success(f"Aula '{nuova_aula}' aggiunta con successo!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Un'aula con questo nome esiste già.")
            else:
                st.warning("Inserisci un nome valido.")

        st.markdown("---")
        aula_da_eliminare = st.selectbox("Seleziona aula da eliminare", get_lista_aule())
        if st.button("Elimina Aula"):
            cursor.execute("DELETE FROM aule WHERE nome = ?", (aula_da_eliminare,))
            conn.commit()
            st.success(f"Aula '{aula_da_eliminare}' eliminata.")
            st.rerun()