import sqlite3

DB_NAME = "audit_energetique.db"

raw_data = """
janv-24	525461	61273	540641	333302	455212	239067
févr-24	609678	49560	649604	267110	393474	222359
mars-24	620849	51389	713596	232074	393082	275757
avr-24	546800	55983	581472	250029	341359	102541
mai-24	551098	44130	806944	239875	298403	263385
juin-24	616679	34580	754379	201396	226456	203539
juil-24	549896	56078	690543	234085	236903	227328
août-24	547605	57684	519100	132705	314490	213071
sept-24	578173	61496	572939	230436	414781	281309
oct-24	667765	63646	698991	290736	398729	145521
nov-24	620831	66044	661611	263955	486819	133410
déc-24	633033	50589	724511	206848	430531	203759
janv-23	712285	75599	638933	255871	415440	291229
févr-23	664239	86567	594056	324902	447799	299718
mars-23	665842	71346	758134	272618	451208	310528
avr-23	547559	58488	500055	185235	372471	220415
mai-23	592636	56012	870225	268605	364416	249798
juin-23	581552	51391	627773	266353	278978	282516
juil-23	597372	61677	587127	240476	184831	208215
août-23	534833	69531	621126	220725	165810	172547
sept-23	649914	64026	679214	283346	407917	274128
oct-23	613881	77987	620770	296325	411799	142764
nov-23	556047	26619	542276	269275	467863	230250
déc-23	574251	20172	559651	101667	489244	168743
janv-22	626126	59008	796786	199916	400842	113454
févr-22	597510	80473	809077	218537	446781	230171
mars-22	609146	67376	975609	253113	484920	298216
avr-22	525653	42518	882738	223365	368553	196308
mai-22	527121	48101	841709	269517	369818	244310
juin-22	532468	46792	840069	204908	230710	239760
juil-22	587617	44431	671784	134905	214553	243591
août-22	521553	76813	651971	206209	255678	284040
sept-22	607413	49124	471992	224976	371288	265687
oct-22	583454	76545	679991	238159	403817	311117
nov-22	858272	67064	704272	297873	400927	369531
déc-22	495115	74461	721406.888	291427.644	410143.294	339161.31
"""

def parse_month(m_str):
    mapping = {
        "janv": 1, "févr": 2, "mars": 3, "avr": 4,
        "mai": 5, "juin": 6, "juil": 7, "août": 8,
        "sept": 9, "oct": 10, "nov": 11, "déc": 12
    }
    parts = m_str.split('-')
    month = mapping[parts[0].lower()]
    year = 2000 + int(parts[1])
    # On fixe au 28 du mois pour être cohérent avec les factures
    return f"{year}-{month:02d}-28"

def run_integration():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Créer la table si ce n'est pas déjà fait
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_production DATE NOT NULL,
            unite_mesure TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            scope_value TEXT NOT NULL,
            quantite REAL NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    total_added = 0
    for line in raw_data.strip().split('\n'):
        if not line: continue
        parts = line.split()
        if len(parts) != 7: continue
        
        date_str = parse_month(parts[0])
        p1 = float(parts[2].replace(',', '.'))
        p2 = float(parts[3].replace(',', '.'))
        p3 = float(parts[4].replace(',', '.'))
        p4 = float(parts[5].replace(',', '.'))
        p5 = float(parts[6].replace(',', '.'))
        
        prods = [("P1", p1), ("P2", p2), ("P3", p3), ("P4", p4), ("P5", p5)]
        
        for name, quantite in prods:
            cursor.execute('''
                INSERT INTO production (
                    date_production, unite_mesure, scope_type, scope_value, quantite
                ) VALUES (?, 'kg', 'Produit', ?, ?)
            ''', (date_str, name, quantite))
            total_added += 1
            
    conn.commit()
    conn.close()
    print(f"✅ {total_added} lignes de production insérées (P1-P5 pour 36 mois).")

if __name__ == "__main__":
    run_integration()
