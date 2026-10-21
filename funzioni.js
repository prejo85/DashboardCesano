// Stato dei record caricati nella sessione corrente
let masterDatabase = {
    reparti: [],
    prodotti: [],
    clienti: [],
    canali: []
};

let elencoStore = new Set();
let elencoReparti = new Set();

// Parser numerico per stringhe e valute dei report aziendali (es: 23.923 -> 23923)
function parseNumeric(val) {
    if (!val || val === '-' || val.trim() === "") return 0;
    let clean = val.replace(/\s/g, "").replace(/\./g, "").replace(",", ".");
    return parseFloat(clean) || 0;
}

// Listener principale per il caricamento contemporaneo dei file locali
document.getElementById('fileUploader').addEventListener('change', function(e) {
    const files = e.target.files;
    const badgeContainer = document.getElementById('loadedFiles');
    badgeContainer.innerHTML = ""; // Svuota i vecchi caricamenti
    
    let processedFiles = 0;
    for (let i = 0; i < files.length; i++) {
        let file = files[i];
        
        const span = document.createElement('span');
        span.className = 'file-badge';
        span.innerText = `📄 ${file.name}`;
        badgeContainer.appendChild(span);

        let reader = new FileReader();
        reader.onload = function(evt) {
            parseAndInsertRows(evt.target.result);
            processedFiles++;
            // Quando tutti i file scelti sono stati letti, aggiorna i filtri e l'interfaccia
            if (processedFiles === files.length) {
                costruisciFiltriTendina();
                aggiornaTutteLeInterrogazioni();
            }
        };
        reader.readAsText(file);
    }
});

// Separatore righe CSV/TXT del report gestionale
function parseCSV(text) {
    const lines = text.split("\n");
    return lines.map(line => line.replace(/"/g, "").split(";").map(c => c.trim()))
                .filter(row => row.length > 1 && row !== "");
}
function parseAndInsertRows(text) {
    const rows = parseCSV(text);
    if (rows.length === 0) return;

    const headerRow = rows.find(r => r.includes("Sales Department") || r.includes("Article") || r.includes("CTG") || r.includes("Customer"));
    if (!headerRow) return;

    const dataRows = rows.slice(rows.indexOf(headerRow) + 1);

    // 1. MAPPATURA: FILE REPARTI (bmplreparti o Mensilizzazione)
    if (headerRow.includes("Sales Department") && headerRow.includes("Front Margin") && !headerRow.includes("Channel Detail")) {
        dataRows.forEach(r => {
            if(!r || r === "" || r[1] === "Sales Department" || r[1] === "") return;
            let storeInferred = "0011 - CESANO BOSCONE"; 
            elencoStore.add(storeInferred);
            elencoReparti.add(r[1]);
            masterDatabase.reparti.push({
                store: storeInferred,
                f_nf: r[0],
                reparto: r[1],
                sales: parseNumeric(r[3] || r[5]), // Compatibilità colonne tracciati diversi
                py: parseNumeric(r[4] || r[8]),
                colli: parseNumeric(r[5] || r[7]),
                margin: parseNumeric(r[7] || r[11])
            });
        });
    }
    // 2. MAPPATURA: FILE ARTICOLI INDISPENSABILI
    else if (headerRow.includes("Article") && headerRow.includes("DA - Sales TT")) {
        dataRows.forEach(r => {
            if(!r || r[4] === "") return;
            elencoReparti.add(r[2]);
            masterDatabase.prodotti.push({
                store: "0011 - CESANO BOSCONE",
                art: r[4],
                g2: r[3],
                sales: parseNumeric(r[5]),
                py: parseNumeric(r[6]),
                colli: parseNumeric(r[7]),
                mperc: r[9]
            });
        });
    }
    // 3. MAPPATURA: FILE ANALYSIS SELLOUT PETROCELLI (Clienti)
    else if (headerRow.includes("Customer") && headerRow.includes("Sales TT")) {
        dataRows.forEach(r => {
            if(!r || r[6] === "") return;
            elencoStore.add(r[0]);
            elencoReparti.add(r[2]);
            masterDatabase.clienti.push({
                store: r[0],
                reparto: r[2],
                name: r[4],
                type: r[6],
                agent: r[8],
                sales: parseNumeric(r[11]),
                margin: parseNumeric(r[19])
            });
        });
    }
    // 4. MAPPATURA: FILE CANALI / CTG
    else if (headerRow.includes("CTG") && headerRow.includes("Channel Detail")) {
        dataRows.forEach(r => {
            if(!r || r[4] === "") return;
            elencoReparti.add(r[1]);
            masterDatabase.canali.push({
                store: "0011 - CESANO BOSCONE",
                dep: r[1],
                ch: r[2],
                ctg: r[4],
                promo: r[5],
                sales: parseNumeric(r[7]),
                py: parseNumeric(r[8])
            });
        });
    }
}

// Costruzione dinamica degli elenchi tendina in base agli Store e Reparti trovati
function costruisciFiltriTendina() {
    const listStoreId = ['storeOverview', 'storeReparti', 'storeProdotti', 'storeClienti', 'storeCanali'];
    const listRepartiId = ['repartoOverview', 'repartoReparti', 'repartoProdotti', 'repartoClienti', 'repartoCanali'];

    if(elencoStore.size === 0) elencoStore.add("0011 - CESANO BOSCONE");

    listStoreId.forEach(id => {
        const select = document.getElementById(id);
        if(select) select.innerHTML = Array.from(elencoStore).map(s => `<option value="${s}">${s}</option>`).join('');
    });

    listRepartiId.forEach(id => {
        const select = document.getElementById(id);
        if(select) select.innerHTML = '<option value="">Tutti i Reparti</option>' + Array.from(elencoReparti).map(r => `<option value="${r}">${r}</option>`).join('');
    });
}

function aggiornaTutteLeInterrogazioni() {
    filtraTabOverview();
    filtraTabReparti();
    filtraTabProdotti();
    filtraTabClienti();
    filtraTabCanali();
}
function filtraTabOverview() {
    const store = document.getElementById("storeOverview").value;
    const rep = document.getElementById("repartoOverview").value;
    
    let filtered = masterDatabase.reparti;
    if(store) filtered = filtered.filter(r => r.store === store);
    if(rep) filtered = filtered.filter(r => r.reparto === rep);

    let tot = 0; let totPY = 0; let margin = 0;
    filtered.forEach(x => { tot += x.sales; totPY += x.py; margin += x.margin; });

    const perc = tot > 0 ? ((margin / tot) * 100).toFixed(2) : '0.00';
    const delta = totPY > 0 ? (((tot - totPY) / totPY) * 100).toFixed(2) : '0.00';

    document.getElementById("kpiFatturato").innerText = `€ ${tot.toLocaleString('it-IT', {maximumFractionDigits:2})}`;
    document.getElementById("kpiFatturatoPY").innerText = `€ ${totPY.toLocaleString('it-IT', {maximumFractionDigits:2})}`;
    document.getElementById("kpiMargine").innerText = `€ ${margin.toLocaleString('it-IT', {maximumFractionDigits:2})}`;
    document.getElementById("kpiMarginePerc").innerText = `${perc}%`;
    document.getElementById("kpiDelta").innerText = `${parseFloat(delta) >= 0 ? '▲ +' : '▼ '}${delta}% vs PY`;
    document.getElementById("kpiDelta").style.color = parseFloat(delta) >= 0 ? '#10b981' : '#ef4444';

    Plotly.newPlot('overviewTrendChart', [
        { x: filtered.map(f=>f.reparto), y: filtered.map(f=>f.sales), name: 'Corrente 2026 (€)', type: 'bar', marker:{color:'#1e3a8a'} },
        { x: filtered.map(f=>f.reparto), y: filtered.map(f=>f.py), name: 'Precedente PY (€)', type: 'bar', marker:{color:'#93c5fd'} }
    ], { barmode: 'group', height: 350, margin: { t: 30, b: 80, l: 60, r: 10 } });
}

function filtraTabReparti() {
    const store = document.getElementById("storeReparti").value;
    const rep = document.getElementById("repartoReparti").value;
    const body = document.getElementById("bodyReparti");
    body.innerHTML = "";

    let filtered = masterDatabase.reparti;
    if(store) filtered = filtered.filter(r => r.store === store);
    if(rep) filtered = filtered.filter(r => r.reparto === rep);

    if(filtered.length === 0) { body.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">Nessun record corrispondente.</td></tr>'; return; }

    filtered.forEach(r => {
        body.innerHTML += `<tr>
            <td>${r.store}</td>
            <td><span class="badge-food">${r.f_nf}</span></td>
            <td>${r.reparto}</td>
            <td class="num">€ ${r.sales.toLocaleString('it-IT', {minimumFractionDigits:2})}</td>
            <td class="num">€ ${r.py.toLocaleString('it-IT', {minimumFractionDigits:2})}</td>
            <td class="num">${r.colli.toLocaleString('it-IT')}</td>
            <td class="num">€ ${r.margin.toLocaleString('it-IT', {minimumFractionDigits:2})}</td>
        </tr>`;
    });
}

function filtraTabProdotti() {
    const rep = document.getElementById("repartoProdotti").value;
    const body = document.getElementById("bodyProdotti");
    body.innerHTML = "";

    let filtered = masterDatabase.prodotti;
    if(rep) {
        let cleanRep = rep.replace(/\d+\s*-\s*/, "").toUpperCase();
        filtered = filtered.filter(p => p.art.toUpperCase().includes(cleanRep) || p.g2.toUpperCase().includes(cleanRep));
    }

    if(filtered.length === 0) { body.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">Nessun record trovato. Inserisci il file prodotti.</td></tr>'; return; }

    filtered.forEach(p => {
        body.innerHTML += `<tr><td>${p.store}</td><td><strong>${p.art}</strong></td><td>${p.g2}</td><td class="num">€ ${p.sales.toLocaleString('it-IT', {minimumFractionDigits:2})}</td><td class="num">€ ${p.py.toLocaleString('it-IT', {minimumFractionDigits:2})}</td><td class="num">${p.colli.toLocaleString('it-IT')}</td><td class="num" style="color:#16a34a; font-weight:600;">${p.mperc}%</td></tr>`;
    });
}

// Filtra i clienti in base a Store e Reparto selezionati nella Tab 4
function filtraTabClienti() {
    const store = document.getElementById("storeClienti").value;
    const rep = document.getElementById("repartoClienti").value;
    const body = document.getElementById("bodyClienti");
    body.innerHTML = "";

    let filtered = masterDatabase.clienti;
    if(store) filtered = filtered.filter(c => c.store === store);
    if(rep) filtered = filtered.filter(c => c.reparto === rep);

    if(filtered.length === 0) { body.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">Nessun record trovato. Inserisci il file clienti.</td></tr>'; return; }

    filtered.forEach(c => {
        body.innerHTML += `<tr><td>${c.store}</td><td>${c.reparto}</td><td>${c.name}</td><td>${c.type}</td><td>${c.agent}</td><td class="num">€ ${c.sales.toLocaleString('it-IT', {minimumFractionDigits:2})}</td><td class="num">€ ${c.margin.toLocaleString('it-IT', {minimumFractionDigits:2})}</td></tr>`;
    });
}

function filtraTabCanali() {
    const rep = document.getElementById("repartoCanali").value;
    const body = document.getElementById("bodyCanali");
    body.innerHTML = "";

    let filtered = masterDatabase.canali;
    if(rep) filtered = filtered.filter(ch => ch.dep === rep);

    if(filtered.length === 0) { body.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">Nessun record trovato. Inserisci il file canali (ctg).</td></tr>'; return; }

    filtered.forEach(ch => {
        body.innerHTML += `<tr><td>${ch.store}</td><td>${ch.dep}</td><td>${ch.ch}</td><td>${ch.ctg}</td><td>${ch.promo}</td><td class="num">€ ${ch.sales.toLocaleString('it-IT', {minimumFractionDigits:2})}</td><td class="num">€ ${ch.py.toLocaleString('it-IT', {minimumFractionDigits:2})}</td></tr>`;
    });
}

// Navigazione schede e filtri di ricerca interni alle tabelle
function switchTab(evt, tabId) {
    const contents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < contents.length; i++) contents[i].classList.remove("active");
    const buttons = document.getElementsByClassName("tab-button");
    for (let i = 0; i < buttons.length; i++) buttons[i].classList.remove("active");
    document.getElementById(tabId).classList.add("active");
    evt.currentTarget.classList.add("active");
}

function runLocalTableSearch(tableId, inputId) {
    const filter = document.getElementById(inputId).value.toUpperCase();
    const rows = document.getElementById(tableId).getElementsByTagName("tr");
    for (let i = 1; i < rows.length; i++) {
        let m = false; const cells = rows[i].getElementsByTagName("td");
        for (let j = 0; j < cells.length; j++) { if (cells[j] && cells[j].innerText.toUpperCase().indexOf(filter) > -1) { m = true; break; } }
        rows[i].style.display = m ? "" : "none";
    }
}
