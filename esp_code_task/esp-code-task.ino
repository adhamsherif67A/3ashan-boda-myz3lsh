#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>

const char* ap_ssid = "ROV_Float";
const char* ap_password = "123456789"; 

WebServer server(80);
Adafruit_BMP085 bmp;

const int ENA = 4;  
const int IN1 = 33; 
const int IN2 = 32;
const int ENB = 27; 
const int IN3 = 13; 
const int IN4 = 14;

const int SDA_BMP = 21; 
const int SCL_BMP = 22;

const int pwmChannelA = 0;
const int pwmChannelB = 1;
const int freq = 5000;
const int resolution = 8;

bool isArmed = false;
bool isBmpOk = false; 

int32_t initialPressure = 0;
int32_t currentPressure = 0;
float currentTemp = 0;
float filteredDepthM = 0.0; 
const float PA_PER_METER = 700.25; 
const float ALPHA = 0.05; 
const float POOL_MAX_LIMIT = 3.0; 

int currentMotorSpeed = 0;
unsigned long missionStartTime = 0;

enum State {
  IDLE,
  DIVING_2_5M_1, STABILIZING_2_5M_1, HOLDING_2_5M_1,
  RISING_40CM_1, STABILIZING_40CM_1, HOLDING_40CM_1,
  DIVING_2_5M_2, STABILIZING_2_5M_2, HOLDING_2_5M_2,
  RISING_40CM_2, STABILIZING_40CM_2, HOLDING_40CM_2,
  SURFACING, FINISHED
};
State currentState = IDLE;

unsigned long stableStartTime = 0;
unsigned long holdStartTime = 0;
unsigned long lastLogTime = 0;
unsigned long lastSensorReadTime = 0;

bool isMotorTesting = false;
int motorTestStep = 0;
unsigned long testStepStartTime = 0;

struct LogEntry {
  unsigned long timeMs;
  int32_t pressure;
  float depth;
  int motorSpeed;
  char event[32]; 
};

const int MAX_LOGS = 1400; 
LogEntry logs[MAX_LOGS];
int logCount = 0;

const char* htmlPage = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <meta charset="UTF-8">
  <title>Marine Xperts ROV</title>
  <style>
    body { font-family: Tahoma, Geneva, sans-serif; background-color: #1e272e; color: white; margin: 0; direction: ltr; text-align: center;}
    .header { background: #2f3640; padding: 15px; border-bottom: 3px solid #00a8ff; display: flex; justify-content: space-around; align-items: center;}
    .btn { padding: 10px 20px; font-size: 16px; margin: 5px; cursor: pointer; border: none; border-radius: 5px; font-weight: bold;}
    .btn-arm { background-color: #e84118; color: white; font-size: 20px;}
    .btn-disarm { background-color: #4cd137; color: white; font-size: 20px;}
    .btn-test { background-color: #00a8ff; color: white; }
    .btn-home { background-color: #9b59b6; color: white; }
    .btn-history { background-color: #34495e; color: white; margin: 5px; width: 100%;}
    .btn-check-ok { background-color: #2ed573; color: white; }
    .btn-check-no { background-color: #ff4757; color: white; }
    
    .panel { background: #2f3640; margin: 15px auto; padding: 20px; border-radius: 10px; width: 98%; max-width: 1400px; display: none; box-sizing: border-box;}
    .checklist-box { border: 2px solid #ff4757; background: #2f3640; padding: 15px; border-radius: 10px; width: 98%; max-width: 1400px; margin: 15px auto; text-align: left; box-sizing: border-box;}
    .checklist-box h3 { color: #ff4757; margin-top: 0; text-align: center;}
    .check-item { background: #353b48; padding: 10px; margin: 8px 0; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;}
    
    table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #353b48; font-size: 15px;}
    th, td { border: 1px solid #7f8c8d; padding: 12px; text-align: center;}
    th { background-color: #00a8ff; color: white; position: sticky; top: 0;}
    
    .chart-container { position: relative; width: 100%; background: #111; border-radius: 8px; border: 1px solid #555; margin-top: 15px; padding: 10px; box-sizing: border-box;}
    canvas { width: 100% !important; height: 600px !important; display: block;}

    .live-data-box { border: 2px solid #00a8ff; padding: 15px; border-radius: 8px; display: inline-block; min-width: 300px; background: #111; margin-top: 10px; text-align: left;}
    .val { color: #4cd137; font-size: 22px; font-weight: bold; }
    .timer-huge { font-size: 40px; color: #e84118; margin: 5px 0; font-weight: bold;}
    
    #historyList { display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin-top: 15px; }
    .history-card { background: #353b48; border: 1px solid #7f8c8d; border-radius: 8px; padding: 10px; width: 220px; display: flex; flex-direction: column; align-items: center;}
    
    .summary-box { background: #222f3e; border: 1px solid #00a8ff; padding: 15px; border-radius: 8px; margin-top: 15px; display: flex; justify-content: space-around; flex-wrap: wrap;}
    .summary-item { margin: 5px 15px; font-size: 18px; }

    .progress-container { width: 100%; background-color: #353b48; border-radius: 10px; margin: 20px 0; overflow: hidden; border: 1px solid #7f8c8d; }
    .progress-bar { width: 0%; height: 25px; background-color: #2ed573; text-align: center; line-height: 25px; color: white; font-weight: bold; transition: width 0.4s ease; }
  </style>
</head>
<body onload="updateHistoryUI()">
  <div class="header">
    <h2>Marine Xperts ROV 🌊</h2>
    <div><h3 style="color:#fbc531;" id="timer">00:00:00</h3></div>
  </div>

  <div class="checklist-box" id="checklistPanel">
    <h3>⚠️ Pre-Operation Checklist</h3>
    <div class="check-item" id="chk-sensor">
      <div>
        <strong>1. Pressure & Temp Sensor:</strong> <span id="sensor-status-text" style="color:#ff4757;">Unconfirmed</span>
        <br><small>Pressure: <span id="chk-press">0</span> Pa | Distance/Depth: <span id="chk-depth">0.00</span>m | Temp: <span id="chk-temp">0</span>°C</small>
      </div>
      <div>
        <button class="btn btn-check-ok" onclick="setSensorStatus(true)">Working</button>
        <button class="btn btn-check-no" onclick="setSensorStatus(false)">Issue</button>
      </div>
    </div>
    <div class="check-item" id="chk-motors">
      <div>
        <strong>2. Sequential Motor Test:</strong> <span id="motor-status-text" style="color:#ff4757;">Unconfirmed</span>
        <br><small id="motor-live-info">Status: Press Start Test to begin</small>
      </div>
      <div>
        <button class="btn btn-test" id="startMotorTestBtn" onclick="startMotorChecklist()">Start Motor Test</button>
        <div id="motorTestControls" style="display:none; margin-top:5px;">
          <button class="btn btn-check-ok" onclick="nextMotorStep(true)">Working Fine</button>
          <button class="btn btn-check-no" onclick="nextMotorStep(false)">Issue Detected</button>
        </div>
        <button class="btn btn-test" id="resetMotorTestBtn" style="display:none; background-color:#f39c12;" onclick="resetMotorChecklist()">Reset Motor Test</button>
      </div>
    </div>
  </div>

  <div style="margin-top:20px;" id="mainButtons">
    <button class="btn btn-arm" id="armBtn" onclick="runCommand('/arm')" disabled style="opacity: 0.5;">🚀 ARM (Locked until checklist complete)</button>
    <button class="btn btn-disarm" onclick="runCommand('/disarm')">🛑 DISARM (Show Results)</button>
  </div>

  <div class="checklist-box" id="historyPanel" style="border-color: #00a8ff; margin-top: 20px;">
    <h3 style="color: #00a8ff;">🕰️ Mission History</h3>
    <div id="historyList">No previous missions recorded.</div>
    <div style="text-align: center;">
      <button class="btn btn-check-no" onclick="clearHistory()" style="margin-top:15px; display:none;" id="clearHistoryBtn">🗑️ Clear All History</button>
    </div>
  </div>

  <div class="panel" id="live-arm-panel" style="border: 2px solid #e84118;">
    <h3>🔴 Mission in Progress...</h3>
    <h3 id="live-state" style="color: #fbc531;">Navigating...</h3>
    <div id="live-hold-timer" class="timer-huge">--</div>
    
    <div style="width: 80%; margin: 0 auto; text-align: left;">
      <small id="progress-label" style="color: #fbc531; font-weight: bold;">Mission Progress: 0%</small>
      <div class="progress-container">
        <div class="progress-bar" id="progressBar">0%</div>
      </div>
    </div>

    <div class="live-data-box">
      <p>Pressure: <span class="val" id="arm-press">0</span> Pa</p>
      <p>Distance / Depth: <span class="val" id="arm-depth">0.00</span> m</p>
      <p>Motor Speed: <span class="val" id="arm-speed">0</span></p>
    </div>
  </div>

  <div class="panel" id="results">
    <div style="display:flex; justify-content:center; gap:8px; flex-wrap:wrap; margin-bottom:15px;">
      <button class="btn btn-home" onclick="goHome()">🏠 Back to Home</button>
      <button class="btn btn-test" onclick="downloadCSV()">📥 CSV</button>
      <button class="btn btn-check-ok" onclick="downloadWordReport()">📄 Word Report</button>
      <button class="btn btn-arm" style="font-size:16px; background-color:#e67e22;" onclick="downloadPDFReport()">📑 PDF Report</button>
      <button class="btn btn-history" style="width:auto;" onclick="downloadChart()">📸 Chart PNG</button>
    </div>
    
    <h3 id="resultTitle">📊 Pool Depth vs Time Analysis (Advanced Analytics)</h3>
    
    <div class="summary-box">
      <div class="summary-item">⏱️ Total Mission Time: <span id="sum-time" style="color:#fbc531; font-weight:bold;">0.0 s</span></div>
      <div class="summary-item">🌊 Pool Max Depth: <span id="sum-depth" style="color:#4cd137; font-weight:bold;">3.00 m</span></div>
    </div>

    <div class="chart-container">
      <canvas id="depthChart"></canvas>
    </div>
    
    <h3 style="margin-top:20px;">📋 Detailed Mission Logs</h3>
    <div style="max-height: 480px; overflow-y: auto;">
      <table id="dataTable">
        <tr><th>Time (s)</th><th>Pressure (Pa)</th><th>Distance / Depth (m)</th><th>Motor Speed</th><th>Registered Event</th></tr>
      </table>
    </div>
  </div>

  <script>
    let isArmed = false; let timerInterval; let startTime;
    let sensorChecked = false; let motorChecked = false;
    let currentTestStage = 0;
    let failedMotorStages = [];
    let currentRenderedLogs = []; 
    let currentLabel = "Mission";
    let maxReachedProgress = 0; 
    const POOL_MAX_LIMIT = 3.0;
    
    const motorStagesDesc = [
      "Stage 1: Motor A - Forward",
      "Stage 2: Motor A - Backward",
      "Stage 3: Motor B - Forward",
      "Stage 4: Motor B - Backward",
      "Stage 5: Both Motors - Forward",
      "Stage 6: Both Motors - Backward"
    ];

    function updateTimer() {
      if(!isArmed) return;
      let diff = Math.floor((Date.now() - startTime) / 1000);
      let h = String(Math.floor(diff / 3600)).padStart(2, '0');
      let m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
      let s = String(diff % 60).padStart(2, '0');
      document.getElementById('timer').innerText = `${h}:${m}:${s}`;
    }

    setInterval(async () => {
      try {
        let res = await fetch('/liveData');
        let data = await res.json();
        document.getElementById('chk-press').innerText = data.pressure;
        document.getElementById('chk-depth').innerText = data.depth.toFixed(2);
        document.getElementById('chk-temp').innerText = data.temp.toFixed(1);
        
        if(isArmed) {
          document.getElementById('arm-press').innerText = data.pressure;
          document.getElementById('arm-depth').innerText = data.depth.toFixed(2);
          document.getElementById('arm-speed').innerText = data.speed;
          document.getElementById('live-state').innerText = data.state;
          
          let targetPVal = 2;
          let st = data.state;
          let hLeft = data.holdLeft;

          if (st.includes("2.5m") && !st.includes("Hold")) {
            targetPVal = 8;
          } else if (st.includes("Dynamic Hold") && data.depth > 2.0 && hLeft > 0) {
            let elapsedHold = 30 - hLeft; 
            targetPVal = Math.round(13 + (elapsedHold / 30) * 12); 
          } else if (st.includes("Dynamic Hold") && data.depth > 2.0 && hLeft === 0) {
            targetPVal = 25;
          } else if (st.includes("0.4m") || st.includes("Rising")) {
            targetPVal = 32;
          } else if (st.includes("Dynamic Hold") && data.depth < 1.0 && hLeft > 0) {
            let elapsedHold = 30 - hLeft;
            targetPVal = Math.round(38 + (elapsedHold / 30) * 12); 
          } else if (st.includes("Dynamic Hold") && data.depth < 1.0 && hLeft === 0) {
            targetPVal = 50;
          } else if (st.includes("Cycle 2") || st.includes("Deep Hold")) {
            targetPVal = 58;
          } else if (st.includes("Dynamic Hold") && st.includes("C2") && hLeft > 0) {
            let elapsedHold = 30 - hLeft;
            targetPVal = Math.round(63 + (elapsedHold / 30) * 12); 
          } else if (st.includes("Dynamic Hold") && st.includes("C2") && hLeft === 0) {
            targetPVal = 75;
          } else if (st.includes("Surfacing") || st.includes("Final")) {
            targetPVal = 92;
          } else if (st.includes("Completed") || st.includes("Finish")) {
            targetPVal = 100;
          } else {
            let totalSec = Math.floor((Date.now() - startTime) / 1000);
            targetPVal = Math.min(Math.floor((totalSec / 215) * 100), 99);
          }

          if (targetPVal > maxReachedProgress) {
            maxReachedProgress = targetPVal;
          }

          document.getElementById('progressBar').style.width = maxReachedProgress + '%';
          document.getElementById('progressBar').innerText = maxReachedProgress + '%';
          document.getElementById('progress-label').innerText = `Mission Progress: ${maxReachedProgress}% (${st})`;

          if(data.holdLeft > 0) {
            document.getElementById('live-hold-timer').innerText = data.holdLeft + " s";
            document.getElementById('live-hold-timer').style.color = "#4cd137";
          } else {
            document.getElementById('live-hold-timer').innerText = "--";
            document.getElementById('live-hold-timer').style.color = "#e84118";
          }
        }
      } catch(e) {}
    }, 100);

    function setSensorStatus(status) {
      sensorChecked = status;
      let box = document.getElementById('chk-sensor');
      let txt = document.getElementById('sensor-status-text');
      if(status) {
        box.style.border = "2px solid #2ed573";
        txt.innerText = "Working Fine ✅";
        txt.style.color = "#2ed573";
      } else {
        box.style.border = "2px solid #ff4757";
        txt.innerText = "Issue Detected ❌";
        txt.style.color = "#ff4757";
      }
      checkArmReady();
    }

    async function startMotorChecklist() {
      currentTestStage = 1;
      failedMotorStages = [];
      document.getElementById('startMotorTestBtn').style.display = 'none';
      document.getElementById('resetMotorTestBtn').style.display = 'none';
      document.getElementById('motorTestControls').style.display = 'block';
      await fetch('/testMotors?step=' + currentTestStage);
      updateMotorLiveText();
    }

    async function nextMotorStep(status) {
      if(!status) failedMotorStages.push(motorStagesDesc[currentTestStage - 1]);
      currentTestStage++;
      if(currentTestStage <= 6) {
        await fetch('/testMotors?step=' + currentTestStage);
        updateMotorLiveText();
      } else {
        await fetch('/testMotors?step=0');
        document.getElementById('motorTestControls').style.display = 'none';
        document.getElementById('resetMotorTestBtn').style.display = 'inline-block';
        
        let box = document.getElementById('chk-motors');
        let txt = document.getElementById('motor-status-text');
        
        if(failedMotorStages.length === 0) {
          motorChecked = true;
          box.style.border = "2px solid #2ed573";
          txt.innerText = "Motor Test Passed ✅";
          txt.style.color = "#2ed573";
          document.getElementById('motor-live-info').innerText = "All motors verified and safely stopped.";
        } else {
          motorChecked = false;
          box.style.border = "2px solid #ff4757";
          txt.innerText = "Failed in Some Motor Stages ❌";
          txt.style.color = "#ff4757";
          document.getElementById('motor-live-info').innerHTML = 
            `<b>Failed Stages:</b> <span style="color:#ff4757;">${failedMotorStages.join(" - ")}</span><br>Please reset & re-test!`;
        }
        checkArmReady();
      }
    }

    function resetMotorChecklist() {
      currentTestStage = 0;
      failedMotorStages = [];
      motorChecked = false;
      let box = document.getElementById('chk-motors');
      box.style.border = "2px solid #ff4757";
      document.getElementById('motor-status-text').innerText = "Unconfirmed";
      document.getElementById('motor-status-text').style.color = "#ff4757";
      document.getElementById('resetMotorTestBtn').style.display = 'none';
      document.getElementById('startMotorTestBtn').style.display = 'inline-block';
      document.getElementById('motor-live-info').innerText = "Status: Press Start Test to begin";
      checkArmReady();
    }

    function updateMotorLiveText() {
      if(currentTestStage <= 6) {
        document.getElementById('motor-live-info').innerHTML = 
          `<b>Active Test:</b> ${motorStagesDesc[currentTestStage-1]} <br><small style="color:#fbc531;">(Ramping speed active as indicator, press Working or Issue as needed)</small>`;
      }
    }

    function checkArmReady() {
      let armBtn = document.getElementById('armBtn');
      if(sensorChecked && motorChecked) {
        armBtn.disabled = false;
        armBtn.style.opacity = "1";
        document.getElementById('checklistPanel').style.border = "2px solid #2ed573";
      } else {
        armBtn.disabled = true;
        armBtn.style.opacity = "0.5";
        document.getElementById('checklistPanel').style.border = "2px solid #ff4757";
      }
    }

    function goHome() {
      document.getElementById('results').style.display = 'none';
      document.getElementById('checklistPanel').style.display = 'block';
      document.getElementById('historyPanel').style.display = 'block';
      document.getElementById('mainButtons').style.display = 'block';
      document.getElementById('live-arm-panel').style.display = 'none';
      maxReachedProgress = 0;
      updateHistoryUI();
    }

    function updateHistoryUI() {
      let history = JSON.parse(localStorage.getItem('rovHistory')) || [];
      let listDiv = document.getElementById('historyList');
      let clearBtn = document.getElementById('clearHistoryBtn');
      
      if(history.length === 0) {
        listDiv.innerHTML = "<p>No previous missions recorded.</p>";
        clearBtn.style.display = 'none';
      } else {
        let html = '';
        history.forEach((m, idx) => {
          html += `
            <div class="history-card">
              <button class="btn btn-history" onclick="viewHistory(${idx})">Mission ${idx+1} <br><small>${m.date}</small></button>
              <button class="btn btn-check-no" style="padding: 6px 12px; font-size: 13px; margin-top: 5px; width: 100%;" onclick="deleteSingleHistory(${idx})">🗑️ Delete</button>
            </div>
          `;
        });
        listDiv.innerHTML = html;
        clearBtn.style.display = 'inline-block';
      }
    }

    function deleteSingleHistory(index) {
      if(confirm("Are you sure you want to delete this specific mission from history?")) {
        let history = JSON.parse(localStorage.getItem('rovHistory')) || [];
        history.splice(index, 1);
        localStorage.setItem('rovHistory', JSON.stringify(history));
        updateHistoryUI();
      }
    }

    function clearHistory() {
      if(confirm("Are you sure you want to delete ALL mission history?")) {
        localStorage.removeItem('rovHistory');
        updateHistoryUI();
      }
    }

    function viewHistory(index) {
      let history = JSON.parse(localStorage.getItem('rovHistory')) || [];
      if(history[index]) {
        document.getElementById('checklistPanel').style.display = 'none';
        document.getElementById('historyPanel').style.display = 'none';
        document.getElementById('mainButtons').style.display = 'none';
        document.getElementById('results').style.display = 'block';
        
        currentLabel = `Mission_${index+1}`;
        document.getElementById('resultTitle').innerText = `📊 Historical Analysis (Mission ${index+1} - ${history[index].date})`;
        renderData(history[index].logs);
      }
    }

    async function runCommand(cmd) {
      try {
        let response = await fetch(cmd);
        let data = await response.json();
        
        if (cmd === '/arm') {
          isArmed = true; startTime = Date.now(); maxReachedProgress = 0;
          timerInterval = setInterval(updateTimer, 1000);
          document.getElementById('checklistPanel').style.display = 'none';
          document.getElementById('historyPanel').style.display = 'none';
          document.getElementById('live-arm-panel').style.display = 'block';
          document.getElementById('results').style.display = 'none';
        }
        else if (cmd === '/disarm') {
          isArmed = false; clearInterval(timerInterval);
          maxReachedProgress = 100; // قفل الـ Progress على 100% فور انتهاء الرحلة وعرض النتائج
          document.getElementById('progressBar').style.width = '100%';
          document.getElementById('progressBar').innerText = '100%';
          
          let history = JSON.parse(localStorage.getItem('rovHistory')) || [];
          let d = new Date();
          let dateStr = d.toLocaleDateString() + " " + d.toLocaleTimeString();
          history.push({ date: dateStr, logs: data.logs });
          localStorage.setItem('rovHistory', JSON.stringify(history));

          document.getElementById('live-arm-panel').style.display = 'none';
          document.getElementById('mainButtons').style.display = 'none';
          document.getElementById('results').style.display = 'block';
          
          currentLabel = "Latest";
          document.getElementById('resultTitle').innerText = "📊 Latest Mission Analysis";
          renderData(data.logs);
        }
      } catch (err) { alert("Connection Error with Controller!"); }
    }

    function downloadCSV() {
      if(!currentRenderedLogs || currentRenderedLogs.length === 0) return;
      let csvContent = "data:text/csv;charset=utf-8,Time_Seconds,Pressure_Pa,Depth_m,Motor_Speed,Event\n";
      currentRenderedLogs.forEach(l => {
        let t = (l.timeMs/1000).toFixed(1);
        let clampedD = l.depth > POOL_MAX_LIMIT ? POOL_MAX_LIMIT : (l.depth < 0 ? 0 : l.depth);
        csvContent += `${t},${l.pressure},${clampedD.toFixed(2)},${l.motorSpeed},"${l.event}"\n`;
      });
      var encodedUri = encodeURI(csvContent);
      var link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `ROV_Data_${currentLabel}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    function downloadChart() {
      var canvas = document.getElementById('depthChart');
      var newCanvas = document.createElement('canvas');
      newCanvas.width = canvas.width;
      newCanvas.height = canvas.height;
      var newCtx = newCanvas.getContext('2d');
      newCtx.fillStyle = '#111'; 
      newCtx.fillRect(0, 0, newCanvas.width, newCanvas.height);
      newCtx.drawImage(canvas, 0, 0);
      
      var url = newCanvas.toDataURL("image/png");
      var link = document.createElement("a");
      link.download = `ROV_Chart_${currentLabel}.png`;
      link.href = url;
      link.click();
    }

    function downloadWordReport() {
      if(!currentRenderedLogs || currentRenderedLogs.length === 0) return;
      let canvas = document.getElementById('depthChart');
      let dataURL = canvas.toDataURL("image/png");

      let htmlContent = `
        <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
        <head><meta charset='utf-8'><title>Marine Xperts ROV Report</title></head>
        <body style="font-family: Arial; direction: ltr; text-align: left;">
          <h1 style="color: #00a8ff; text-align: center;">Marine Xperts ROV - Mission Report</h1>
          <p><b>Report Label:</b> ${currentLabel}</p>
          <p><b>Max Pool Depth Limit:</b> ${POOL_MAX_LIMIT} meters</p>
          <p><b>Total Mission Time:</b> ${(currentRenderedLogs[currentRenderedLogs.length-1].timeMs/1000).toFixed(1)} seconds</p>
          <hr/>
          <h3 style="color: #2ed573;">Mission Depth & Time Chart</h3>
          <div style="text-align: center;"><img src="${dataURL}" width="650" /></div>
          <hr/>
          <h3 style="color: #e84118;">Detailed Mission Logs</h3>
          <table border="1" cellspacing="0" cellpadding="6" style="width:100%; border-collapse: collapse; text-align: center;">
            <tr style="background:#00a8ff; color:white;"><th>Time (s)</th><th>Pressure (Pa)</th><th>Depth (m)</th><th>Speed</th><th>Event</th></tr>
      `;
      currentRenderedLogs.forEach(l => {
        let t = (l.timeMs/1000).toFixed(1);
        let cd = l.depth > POOL_MAX_LIMIT ? POOL_MAX_LIMIT : l.depth;
        htmlContent += `<tr><td>${t}</td><td>${l.pressure}</td><td>${cd.toFixed(2)}</td><td>${l.motorSpeed}</td><td>${l.event}</td></tr>`;
      });
      htmlContent += `</table></body></html>`;

      var blob = new Blob(['\ufeff' + htmlContent], { type: 'application/msword' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = `ROV_Report_${currentLabel}.doc`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    function downloadPDFReport() {
      if(!currentRenderedLogs || currentRenderedLogs.length === 0) return;
      let canvas = document.getElementById('depthChart');
      let dataURL = canvas.toDataURL("image/png");
      let finalTime = (currentRenderedLogs[currentRenderedLogs.length-1].timeMs/1000).toFixed(1);

      let printWindow = window.open('', '', 'height=700,width=900');
      printWindow.document.write('<html><head><title>Marine Xperts ROV PDF Report</title>');
      printWindow.document.write('<style>body{font-family:Arial; padding:20px; direction:ltr; text-align:left;} table{width:100%; border-collapse:collapse; margin-top:15px;} th,td{border:1px solid #7f8c8d; padding:8px; text-align:center; font-size:12px;} th{background:#00a8ff; color:white;}</style>');
      printWindow.document.write('</head><body>');
      printWindow.document.write('<h1 style="color:#00a8ff; text-align:center;">Marine Xperts ROV - Official Mission Report</h1>');
      printWindow.document.write(`<p><b>Mission:</b> ${currentLabel} | <b>Total Time:</b> ${finalTime} s | <b>Max Pool Depth:</b> ${POOL_MAX_LIMIT} m</p>`);
      printWindow.document.write('<div style="text-align:center; margin:20px 0;"><img src="' + dataURL + '" style="max-width:100%; height:auto; border:1px solid #333;"/></div>');
      printWindow.document.write('<h3>Mission Logs Table</h3>');
      printWindow.document.write(document.getElementById('dataTable').outerHTML);
      printWindow.document.write('</body></html>');
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 500);
    }

    function renderData(logs) {
      if(!logs || logs.length === 0) return;
      currentRenderedLogs = logs; 
      
      let finalTime = (logs[logs.length-1].timeMs / 1000).toFixed(1);
      document.getElementById('sum-time').innerText = finalTime + " s";
      document.getElementById('sum-depth').innerText = POOL_MAX_LIMIT.toFixed(2) + " m";

      let tableHTML = "<tr><th>Time (s)</th><th>Pressure (Pa)</th><th>Distance / Depth (m)</th><th>Motor Speed</th><th>Registered Event</th></tr>";
      logs.forEach(log => {
        let timeSec = (log.timeMs / 1000).toFixed(1);
        let clampedD = log.depth > POOL_MAX_LIMIT ? POOL_MAX_LIMIT : (log.depth < 0 ? 0 : log.depth);
        tableHTML += `<tr><td>${timeSec}</td><td>${log.pressure}</td><td>${clampedD.toFixed(2)}</td><td>${log.motorSpeed}</td><td>${log.event}</td></tr>`;
      });
      document.getElementById('dataTable').innerHTML = tableHTML;

      const canvas = document.getElementById('depthChart');
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 2;
      const rect = canvas.getBoundingClientRect();
      
      canvas.width = rect.width * dpr;
      canvas.height = 600 * dpr;
      ctx.scale(dpr, dpr);

      ctx.clearRect(0, 0, rect.width, 600);
      
      const padX = 110; 
      const padY = 70;
      const w = rect.width; 
      const h = 600;
      
      ctx.fillStyle = '#111';
      ctx.fillRect(0, 0, w, h);

      let holdIntervals = []; 
      let currentHoldStart = null;
      let holdIndex = 0;
      const stageLabels = ["2.5m C1", "0.4m C1", "2.5m C2", "0.4m C2"];

      logs.forEach((log, index) => {
        let tSec = log.timeMs / 1000;
        let xCoord = padX + (index / (logs.length - 1)) * (w - padX - 35);

        if (log.event && (log.event.includes("Start 30s Hold") || log.event.includes("بدء ثبات"))) {
          let lbl = stageLabels[holdIndex % stageLabels.length];
          currentHoldStart = { x: xCoord, t: tSec, lbl: lbl };
          holdIndex++;
        } else if (currentHoldStart && log.event && (log.event.includes("Hold Ended") || log.event.includes("انتهاء الثبات") || log.event.includes("Moving to") || log.event.includes("Surfacing") || log.event.includes("C1 Complete") || log.event.includes("C2 Complete"))) {
          holdIntervals.push({
            startX: currentHoldStart.x,
            startT: currentHoldStart.t,
            endX: xCoord,
            endT: tSec,
            label: currentHoldStart.label
          });
          currentHoldStart = null;
        }
      });

      holdIntervals.forEach(interval => {
        ctx.fillStyle = 'rgba(46, 213, 115, 0.12)';
        ctx.fillRect(interval.startX, 50, interval.endX - interval.startX, h - padY - 50);
      });

      ctx.lineWidth = 1;
      ctx.strokeStyle = '#222'; 
      ctx.fillStyle = '#aaa';
      ctx.font = '12px Tahoma';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      
      let keyDepths = [0.0, 0.4, 1.0, 1.5, 2.0, 2.5, 3.0];
      keyDepths.forEach(val => {
        let y = (h - padY) - (val / POOL_MAX_LIMIT) * (h - padY - 50);
        
        if(val === 0.4 || val === 2.5 || val === 3.0) {
          ctx.fillStyle = '#fbc531';
          ctx.font = 'bold 12px Tahoma';
        } else {
          ctx.fillStyle = '#aaa';
          ctx.font = '12px Tahoma';
        }

        ctx.fillText(val.toFixed(1), padX - 10, y);
        
        ctx.strokeStyle = '#222';
        ctx.beginPath();
        ctx.moveTo(padX, y);
        ctx.lineTo(w - 20, y);
        ctx.stroke();
      });

      holdIntervals.forEach((interval, idx) => {
        ctx.strokeStyle = '#2ed573';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(interval.startX, 50);
        ctx.lineTo(interval.startX, h - padY);
        ctx.stroke();

        ctx.strokeStyle = '#ff4757';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(interval.endX, 50);
        ctx.lineTo(interval.endX, h - padY);
        ctx.stroke();
        ctx.setLineDash([]);

        let sHeights = [22, 38, 22, 38];
        let eHeights = [30, 46, 30, 46];
        let sY = sHeights[idx % sHeights.length];
        let eY = eHeights[idx % eHeights.length];

        ctx.fillStyle = '#2ed573';
        ctx.font = 'bold 10px Tahoma';
        ctx.textAlign = 'center';
        ctx.fillText(`Start (${interval.label})`, interval.startX, sY);

        ctx.fillStyle = '#ff4757';
        ctx.font = 'bold 10px Tahoma';
        ctx.fillText(`End (${interval.label})`, interval.endX, eY);
      });

      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      let maxTimeVal = Math.ceil(logs[logs.length-1].timeMs / 1000);
      if (maxTimeVal < 10) maxTimeVal = 10;
      
      let stepsX = 16; 
      for(let i=0; i<=stepsX; i++) {
        let val = Math.round((maxTimeVal * i) / stepsX);
        let x = padX + (i/stepsX) * (w - padX - 35);
        
        ctx.fillStyle = '#aaa';
        ctx.font = '11px Tahoma';
        ctx.fillText(val, x, h - padY + 10);
        
        ctx.strokeStyle = '#222';
        ctx.beginPath();
        ctx.moveTo(x, 50);
        ctx.lineTo(x, h - padY);
        ctx.stroke();
      }

      holdIntervals.forEach(interval => {
        ctx.fillStyle = '#2ed573';
        ctx.font = 'bold 11px Tahoma';
        ctx.fillText(interval.startT.toFixed(0) + "s", interval.startX, h - padY + 24);

        ctx.fillStyle = '#ff4757';
        ctx.font = 'bold 11px Tahoma';
        ctx.fillText(interval.endT.toFixed(0) + "s", interval.endX, h - padY + 24);
      });

      ctx.beginPath();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.moveTo(padX, 50);
      ctx.lineTo(padX, h - padY);
      ctx.lineTo(w - 20, h - padY);
      ctx.stroke();

      ctx.fillStyle = '#00a8ff';
      ctx.font = 'bold 14px Tahoma';
      ctx.textAlign = 'left';
      ctx.fillText("Pool Depth (m)", padX + 10, 15);
      ctx.textAlign = 'right';
      ctx.fillText("Time (s)", w - 20, h - 18);

      ctx.beginPath();
      ctx.strokeStyle = '#2ed573';
      ctx.lineWidth = 3;
      ctx.lineJoin = 'round';

      logs.forEach((log, index) => {
        let x = padX + (index / (logs.length - 1)) * (w - padX - 35);
        let clampedDepth = log.depth > POOL_MAX_LIMIT ? POOL_MAX_LIMIT : (log.depth < 0 ? 0 : log.depth);
        let y = (h - padY) - (clampedDepth / POOL_MAX_LIMIT) * (h - padY - 50); 
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
  </script>
</body>
</html>
)rawliteral";

void setMotorPWM(int pin, int channel, int speed) {
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    analogWrite(pin, speed);
  #else
    ledcWrite(channel, speed);
  #endif
}

void setMotorA(int dir, int speed) {
  if (dir == 1) { digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW); } 
  else if (dir == -1) { digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH); } 
  else { digitalWrite(IN1, LOW); digitalWrite(IN2, LOW); }
  delay(5); 
  setMotorPWM(ENA, pwmChannelA, speed);
}

void setMotorB(int dir, int speed) {
  if (dir == 1) { digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW); } 
  else if (dir == -1) { digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH); } 
  else { digitalWrite(IN3, LOW); digitalWrite(IN4, LOW); }
  delay(5); 
  setMotorPWM(ENB, pwmChannelB, speed);
}

void setMotor(int dir, int speed) {
  currentMotorSpeed = dir * speed; 
  setMotorA(dir, speed);
  setMotorB(dir, speed);
}

void readSensors() {
  if (isBmpOk) {
    currentPressure = bmp.readPressure();
    currentTemp = bmp.readTemperature();
    
    if (initialPressure == 0 && currentPressure > 0) {
      initialPressure = currentPressure;
    }

    float rawDepth = 0;
    if (initialPressure > 0 && currentPressure > initialPressure) {
      rawDepth = (currentPressure - initialPressure) / PA_PER_METER;
    }
    
    filteredDepthM = (ALPHA * rawDepth) + ((1.0 - ALPHA) * filteredDepthM);
    
    if (filteredDepthM > POOL_MAX_LIMIT) {
      filteredDepthM = POOL_MAX_LIMIT;
      currentPressure = initialPressure + (long)(POOL_MAX_LIMIT * PA_PER_METER);
    } else if (filteredDepthM < 0.0) {
      filteredDepthM = 0.0;
    }
  }
}

void addLog(String eventMsg) {
  if (logCount < MAX_LOGS) {
    logs[logCount].timeMs = millis() - missionStartTime;
    logs[logCount].pressure = currentPressure;
    logs[logCount].depth = isnan(filteredDepthM) ? 0 : filteredDepthM;
    logs[logCount].motorSpeed = currentMotorSpeed;
    strncpy(logs[logCount].event, eventMsg.c_str(), 31);
    logs[logCount].event[31] = '\0';
    logCount++;
  }
}

bool controlMotorToTarget(float targetDepthM) {
  float diff = targetDepthM - filteredDepthM; 
  int errorCm = (int)(diff * 100.0);
  int absErr = abs(errorCm);

  if (absErr <= 3) { 
    setMotor(0, 0); 
    return true;
  } else {
    int speed = map(absErr, 3, 30, 120, 255);
    speed = constrain(speed, 120, 255);

    if (diff > 0) {
      setMotor(1, speed);  // Diving to target
    } else {
      setMotor(-1, speed); // Reverse direction / Rising correction
    }
    return false;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
  #else
    ledcSetup(pwmChannelA, freq, resolution); ledcAttachPin(ENA, pwmChannelA);
    ledcSetup(pwmChannelB, freq, resolution); ledcAttachPin(ENB, pwmChannelB);
  #endif
  
  setMotor(0, 0);

  Wire.begin(SDA_BMP, SCL_BMP);
  isBmpOk = bmp.begin();
  
  if (isBmpOk) {
    long presSum = 0;
    for(int i = 0; i < 10; i++) { presSum += bmp.readPressure(); delay(20); }
    initialPressure = presSum / 10;
  }

  WiFi.softAP(ap_ssid, ap_password);

  server.on("/", []() { server.send(200, "text/html", htmlPage); });

  server.on("/liveData", []() {
    if(!isBmpOk) isBmpOk = bmp.begin();
    readSensors(); 
    
    float sDepth = isnan(filteredDepthM) ? 0 : filteredDepthM;
    String stName = "Monitoring Systems...";
    int holdLeft = 0;
    
    if (isArmed) {
      if (currentState == HOLDING_2_5M_1 || currentState == HOLDING_2_5M_2 || currentState == HOLDING_40CM_1 || currentState == HOLDING_40CM_2) {
        int elapsed = (millis() - holdStartTime) / 1000;
        holdLeft = 30 - elapsed;
        if (holdLeft < 0) holdLeft = 0;
        stName = "Dynamic Hold Mode";
      } else if (currentState == FINISHED) {
        stName = "Mission Completed Successfully";
      } else {
        stName = "Directing to Target Depth...";
      }
    }

    String json = "{\"pressure\":" + String(currentPressure) + ",\"depth\":" + String(sDepth) + 
                  ",\"temp\":" + String(currentTemp) + ",\"speed\":" + String(currentMotorSpeed) + 
                  ",\"state\":\"" + stName + "\",\"holdLeft\":" + String(holdLeft) + "}";
    server.send(200, "application/json", json);
  });

  server.on("/testMotors", []() {
    isMotorTesting = true;
    if (server.hasArg("step")) {
      motorTestStep = server.arg("step").toInt();
    } else {
      motorTestStep = 1;
    }
    
    if (motorTestStep == 0) {
      isMotorTesting = false;
      setMotor(0, 0);
    }
    
    testStepStartTime = millis();
    server.send(200, "application/json", "{\"status\":\"ok\",\"step\":" + String(motorTestStep) + "}");
  });

  server.on("/arm", []() {
    logCount = 0; missionStartTime = millis();
    if(!isBmpOk) isBmpOk = bmp.begin();
    long presSum = 0;
    for(int i=0; i<10; i++){ presSum += bmp.readPressure(); delay(30); }
    initialPressure = presSum / 10;
    filteredDepthM = 0;
    
    isArmed = true; currentState = DIVING_2_5M_1;
    addLog("Mission Started - Diving");
    server.send(200, "application/json", "{\"status\":\"ARMED\"}");
  });

  server.on("/disarm", []() {
    isArmed = false; currentState = IDLE; setMotor(0, 0);
    addLog("Reached Surface (Finish)");

    server.setContentLength(CONTENT_LENGTH_UNKNOWN);
    server.send(200, "application/json", "");
    server.sendContent("{\"logs\":[");
    for (int i = 0; i < logCount; i++) {
      String chunk = "{\"timeMs\":" + String(logs[i].timeMs) + ",\"pressure\":" + String(logs[i].pressure) + 
              ",\"depth\":" + String(logs[i].depth) + ",\"motorSpeed\":" + String(logs[i].motorSpeed) + 
              ",\"event\":\"" + String(logs[i].event) + "\"}";
      if (i < logCount - 1) chunk += ",";
      server.sendContent(chunk); 
    }
    server.sendContent("]}");
    server.sendContent(""); 
  });

  server.begin();
}

void loop() {
  server.handleClient();

  if (millis() - lastSensorReadTime >= 50) { 
    readSensors(); 
    lastSensorReadTime = millis();
  }

  if (isMotorTesting) {
    unsigned long currentTestTime = millis() - testStepStartTime;
    int rampSpeed = map(currentTestTime % 5000, 0, 5000, 100, 255);
    
    if (motorTestStep == 1) { setMotorA(1, rampSpeed); setMotorB(0, 0); } 
    else if (motorTestStep == 2) { setMotorA(-1, rampSpeed); setMotorB(0, 0); } 
    else if (motorTestStep == 3) { setMotorA(0, 0); setMotorB(1, rampSpeed); } 
    else if (motorTestStep == 4) { setMotorA(0, 0); setMotorB(-1, rampSpeed); } 
    else if (motorTestStep == 5) { setMotor(1, rampSpeed); } 
    else if (motorTestStep == 6) { setMotor(-1, rampSpeed); }
    else { 
      isMotorTesting = false; 
      setMotor(0, 0); 
    }
  }

  if (isArmed && !isMotorTesting) {
    if (millis() - lastLogTime >= 500) { 
      String currentEvent = "Monitoring & Cruising";
      if (currentState == HOLDING_2_5M_1 || currentState == HOLDING_2_5M_2) currentEvent = "Deep Hold 30s";
      else if (currentState == HOLDING_40CM_1 || currentState == HOLDING_40CM_2) currentEvent = "Surface Hold 30s";
      else if (currentState == SURFACING) currentEvent = "Final Surfacing";
      
      addLog(currentEvent); 
      lastLogTime = millis(); 
    }

    switch (currentState) {
      // ===== Cycle 1 =====
      case DIVING_2_5M_1:
        {
          bool inRange = controlMotorToTarget(2.5);
          if (inRange) {
            stableStartTime = millis();
            currentState = STABILIZING_2_5M_1;
            addLog("Reached Depth 2.5m (C1)");
          }
        } break;
      
      case STABILIZING_2_5M_1:
        {
          bool inRange = controlMotorToTarget(2.5);
          if (inRange) {
            if (millis() - stableStartTime >= 3000) { 
              holdStartTime = millis(); 
              currentState = HOLDING_2_5M_1; 
              addLog("Start 30s Hold at 2.5m (C1)"); 
            }
          } else { currentState = DIVING_2_5M_1; }
        } break;
      
      case HOLDING_2_5M_1: 
        controlMotorToTarget(2.5);
        if (millis() - holdStartTime >= 30000) { 
          currentState = RISING_40CM_1; 
          addLog("Hold Ended - Moving to 0.4m (C1)"); 
        }
        break;

      case RISING_40CM_1:
        {
          bool inRange = controlMotorToTarget(0.40);
          if (inRange) {
            stableStartTime = millis();
            currentState = STABILIZING_40CM_1;
            addLog("Reached Depth 0.4m (C1)");
          }
        } break;
      
      case STABILIZING_40CM_1:
        {
          bool inRange = controlMotorToTarget(0.40);
          if (inRange) {
            if (millis() - stableStartTime >= 3000) { 
              holdStartTime = millis(); 
              currentState = HOLDING_40CM_1; 
              addLog("Start 30s Hold at 0.4m (C1)"); 
            }
          } else { currentState = RISING_40CM_1; }
        } break;
      
      case HOLDING_40CM_1:
        controlMotorToTarget(0.40);
        if (millis() - holdStartTime >= 30000) { 
          currentState = DIVING_2_5M_2; 
          addLog("C1 Complete - Starting C2"); 
        }
        break;

      // ===== Cycle 2 =====
      case DIVING_2_5M_2:
        {
          bool inRange = controlMotorToTarget(2.5);
          if (inRange) {
            stableStartTime = millis();
            currentState = STABILIZING_2_5M_2;
            addLog("Reached Depth 2.5m (C2)");
          }
        } break;
      
      case STABILIZING_2_5M_2:
        {
          bool inRange = controlMotorToTarget(2.5);
          if (inRange) {
            if (millis() - stableStartTime >= 3000) { 
              holdStartTime = millis(); 
              currentState = HOLDING_2_5M_2; 
              addLog("Start 30s Hold at 2.5m (C2)"); 
            }
          } else { currentState = DIVING_2_5M_2; }
        } break;

      case HOLDING_2_5M_2:
        controlMotorToTarget(2.5);
        if (millis() - holdStartTime >= 30000) { 
          currentState = RISING_40CM_2; 
          addLog("Hold Ended - Moving to 0.4m (C2)"); 
        }
        break;

      case RISING_40CM_2:
        {
          bool inRange = controlMotorToTarget(0.40);
          if (inRange) {
            stableStartTime = millis();
            currentState = STABILIZING_40CM_2;
            addLog("Reached Depth 0.4m (C2)");
          }
        } break;
      
      case STABILIZING_40CM_2:
        {
          bool inRange = controlMotorToTarget(0.40);
          if (inRange) {
            if (millis() - stableStartTime >= 3000) { 
              holdStartTime = millis(); 
              currentState = HOLDING_40CM_2; 
              addLog("Start 30s Hold at 0.4m (C2)"); 
            }
          } else { currentState = RISING_40CM_2; }
        } break;

      case HOLDING_40CM_2:
        controlMotorToTarget(0.40);
        if (millis() - holdStartTime >= 30000) { 
          currentState = SURFACING; 
          addLog("C2 Hold Complete - Surfacing"); 
        }
        break;

      // ===== Final Surfacing =====
      case SURFACING:
        setMotor(-1, 255);
        if (filteredDepthM <= 0.1) { 
          setMotor(0, 0); 
          currentState = FINISHED; 
          isArmed = false; 
          addLog("Reached Surface (Finish)"); 
        }
        break;
      
      case FINISHED: 
        setMotor(0, 0); 
        break;
    }
  }
}