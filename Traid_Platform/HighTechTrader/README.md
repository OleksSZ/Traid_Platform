# 📚 Документація High-Tech Trader — C# частина

> Мова: Ukrainian | Версія: 1.0 | .NET 10 / WinForms

---

## ЗМІСТ

1. [Загальна картина проекту](#1-загальна-картина-проекту)
2. [Швидкий огляд — за що відповідає кожен файл](#2-швидкий-огляд)
3. [ITrader.cs — контракти та моделі](#3-itradercs)
4. [PythonRunnerBase.cs — базовий клас запуску Python](#4-pythonrunnerbasecs)
5. [TraderService.cs — торгова логіка](#5-traderservicecs)
6. [MonitorService.cs — моніторинг балансу](#6-monitorservicecs)
7. [FreqtradeService.cs — запуск Freqtrade](#7-freqtradeservicecs)
8. [Form1.Designer.cs — розмітка інтерфейсу](#8-form1designercs)
9. [Form1.cs — логіка головної форми](#9-form1cs)
10. [OpenTradeDialog.cs — діалог відкриття позиції](#10-opentradedialogcs)
11. [CloseTradeDialog.cs — діалог закриття позиції](#11-closetradedialogcs)
12. [cs_bridge.py — міст між C# і Python](#12-cs_bridgepy)
13. [Схема взаємодії між файлами](#13-схема-взаємодії)
14. [Складні моменти коду з поясненнями](#14-складні-моменти)

---

## 1. Загальна картина проекту

```
Traid_Platform\
├── HighTechTrader\              ← C# проект (WinForms)
│   ├── Interfaces\
│   │   └── ITrader.cs           ← контракти, моделі, делегати
│   ├── Services\
│   │   ├── PythonRunnerBase.cs  ← базовий клас, запуск Python
│   │   ├── TraderService.cs     ← відкриття/закриття угод
│   │   ├── MonitorService.cs    ← баланс, моніторинг
│   │   └── FreqtradeService.cs  ← запуск Streamlit
│   ├── Forms\
│   │   ├── Form1.cs             ← логіка головного вікна
│   │   ├── Form1.Designer.cs    ← розмітка UI (кнопки, поля)
│   │   ├── OpenTradeDialog.cs   ← діалог підтвердження угоди
│   │   └── CloseTradeDialog.cs  ← діалог закриття позиції
│   └── HighTechTrader.csproj    ← конфігурація проекту
│
├── cs_bridge.py                 ← міст C# → Python модулі
├── trader.py                    ← клас Trader (Binance API)
├── parcer.py                    ← отримання балансу
├── leverage.py                  ← розрахунок плеча
├── checks.py                    ← перевірка RR
└── database.py                  ← запис в Excel журнал
```

**Як це все працює разом:**
C# не виконує торгову логіку сам — він є інтерфейсом.
Коли треба відкрити позицію, C# запускає `cs_bridge.py` з JSON
аргументами, а той вже викликає `trader.py`, `leverage.py` і т.д.
Результат повертається назад як JSON і відображається в логах.

```
[Кнопка у UI]
     │
     ▼
[Form1.cs] → читає поля форми → викликає TraderService
     │
     ▼
[TraderService] → формує JSON → запускає cs_bridge.py
     │
     ▼
[cs_bridge.py] → імпортує trader.py → відкриває позицію на Binance
     │
     ▼
[cs_bridge.py] → повертає {"ok": true, "data": {...}}
     │
     ▼
[TraderService] → парсить JSON → стріляє подією OnTradeOpened
     │
     ▼
[Form1.cs] → виводить результат в лог панель
```

---

## 2. Швидкий огляд

| Файл | Одним реченням |
|------|---------------|
| `ITrader.cs` | Оголошує "правила гри" — інтерфейси, типи подій і моделі даних |
| `PythonRunnerBase.cs` | Вміє запускати будь-який `.py` файл і читати його відповідь |
| `TraderService.cs` | Відповідає за всі торгові операції через `cs_bridge.py` |
| `MonitorService.cs` | Кожні 10 сек оновлює баланс, кожні 3 сек — позиції |
| `FreqtradeService.cs` | Запускає Streamlit інтерфейс Freqtrade у браузері |
| `Form1.Designer.cs` | Визначає як виглядає головне вікно (координати, кольори) |
| `Form1.cs` | Обробляє кліки кнопок, виводить логи, з'єднує все разом |
| `OpenTradeDialog.cs` | Показує деталі угоди перед підтвердженням |
| `CloseTradeDialog.cs` | Дозволяє вибрати позицію і ввести причину закриття |
| `cs_bridge.py` | Єдина точка входу з C# у всі Python модулі |

---

## 3. ITrader.cs

**Розташування:** `Interfaces/ITrader.cs`
**Роль:** Це "словник" всього проекту. Тут немає жодної логіки —
тільки визначення типів. Всі інші файли спираються на ці визначення.

### Делегати

```csharp
public delegate void LogEventHandler(string message);
public delegate void BalanceUpdatedHandler(BalanceInfo balance);
public delegate void TradeOpenedHandler(TradeInfo trade);
public delegate void TradeClosedHandler(string pair, string reason);
```

Делегат — це тип для функції.  "опис підпису функції".

- `LogEventHandler` — будь-яка функція що приймає `string` і нічого не повертає.
  Використовується для передачі лог-повідомлень з сервісів у Form1.
- `BalanceUpdatedHandler` — функція що приймає `BalanceInfo`.
  Викликається коли MonitorService отримав новий баланс з Binance.
- `TradeOpenedHandler` — викликається після успішного відкриття угоди.
- `TradeClosedHandler` — викликається після закриття угоди.

### Моделі даних

```csharp
public class BalanceInfo
{
    public decimal Total       { get; set; }  // весь баланс USDT
    public decimal Available   { get; set; }  // вільні кошти
    public decimal InPositions { get; set; }  // зайнято в позиціях
}
```

```csharp
public class TradeInfo
{
    public string  Pair            { get; set; }  // "BTCUSDT"
    public string  Direction       { get; set; }  // "long" або "short"
    public decimal EntryPrice      { get; set; }  // ціна входу
    public decimal StopLoss        { get; set; }  // стоп-лосс
    public decimal TakeProfit      { get; set; }  // тейк-профіт
    public decimal RiskPercent     { get; set; }  // ризик у відсотках
    public decimal RiskDollar      { get; set; }  // ризик у доларах
    public int     Leverage        { get; set; }  // плече (заповнює TraderService)
    public double  RR              { get; set; }  // RR ratio (заповнює TraderService)
    public string  ReasonEntry     { get; set; }  // причина входу з діалогу
    public int     FearGreed       { get; set; }  // Fear & Greed індекс
    public int     ProfitChance    { get; set; }  // суб'єктивний шанс профіту
    public string  TradingViewLink { get; set; }  // посилання на графік
}
```

`TradeInfo` заповнюється поступово:
- `Form1.cs` заповнює поля форми (Pair, Direction, Entry, Stop, Take, Risk)
- `OpenTradeDialog.cs` додає ReasonEntry, FearGreed, ProfitChance, TradingViewLink
- `TraderService.cs` розраховує і додає Leverage та RR

### Інтерфейси

```csharp
public interface ITrader
{
    event TradeOpenedHandler OnTradeOpened;
    event TradeClosedHandler OnTradeClosed;

    (bool success, string message) OpenTrade(TradeInfo trade);
    (bool success, string message) CloseTrade(string pair, string reason);
    string[] GetOpenPositions();
    string   MonitorTrades();
}
```

```csharp
public interface IMonitor
{
    event BalanceUpdatedHandler OnBalanceUpdated;

    void        StartMonitoring(int intervalMs);
    void        StopMonitoring();
    bool        IsMonitoring { get; }
    BalanceInfo GetBalance();
}
```

Навіщо інтерфейси? Якщо завтра захочеш замінити `TraderService`
на іншу реалізацію (наприклад для іншої біржі) — `Form1.cs` не зміниться,
бо вона працює з інтерфейсом, а не з конкретним класом.

---

## 4. PythonRunnerBase.cs

**Розташування:** `Services/PythonRunnerBase.cs`
**Роль:** Базовий клас для всіх сервісів. Знає як запустити Python процес
і прочитати результат. Містить спільну логіку яку наслідують
`TraderService`, `MonitorService` і `FreqtradeService`.

### Поля

```csharp
protected readonly string PythonExePath;  // шлях до python.exe
protected readonly string ScriptsFolder;  // папка з .py файлами
public event LogEventHandler OnLog;       // подія для передачі логів
```

`protected` — означає що поля доступні в цьому класі і у всіх нащадках,
але не ззовні. `readonly` — можна задати тільки в конструкторі.

### RunScript — синхронний запуск

```csharp
public virtual string RunScript(string scriptPath, string arguments = "")
```

Запускає Python скрипт і **чекає** поки він завершиться.
Повертає весь текст який Python написав у stdout.

**Важливі налаштування ProcessStartInfo:**
```csharp
psi.UseShellExecute        = false;   // не відкривати через Shell (потрібно для Redirect)
psi.CreateNoWindow         = true;    // не показувати чорне вікно консолі
psi.RedirectStandardOutput = true;    // перехоплюємо stdout
psi.RedirectStandardError  = true;    // перехоплюємо stderr
psi.StandardOutputEncoding = Encoding.UTF8;  // щоб emoji не ламались
psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";  // те саме з боку Python
psi.EnvironmentVariables["PYTHONUTF8"]       = "1";
```

**Чому UTF-8 з двох сторін?**
Windows за замовчуванням використовує кодування `cp1252` (Windows-1252).
Emoji як ❌ ✅ не входять в цю таблицю символів і викликають помилку
`'charmap' codec can't encode character`. Тому ми примушуємо і Python
і C# використовувати UTF-8.

### RunScriptAsync — асинхронний запуск

```csharp
public virtual void RunScriptAsync(string scriptPath, string arguments = "")
```

Запускає Python скрипт в **новому вікні** і одразу повертається.
C# не чекає завершення. Використовується для `orderbook_window.py`
який має крутитись у фоні.

Різниця в налаштуваннях:
```csharp
psi.UseShellExecute = true;   // дозволяє відкрити нове вікно
psi.CreateNoWindow  = false;  // показуємо вікно (це потрібно для ордербука)
```

### Log — захищений метод логування

```csharp
protected void Log(string message)
{
    OnLog?.Invoke($"[{DateTime.Now:HH:mm:ss}] {message}");
}
```

`?.` — оператор безпечного виклику. Якщо ніхто не підписався на `OnLog`
(тобто OnLog == null) — нічого не станеться, помилки не буде.
Всі нащадки (TraderService, MonitorService) викликають `Log()` щоб
передати повідомлення у Form1 через ланцюжок подій.

---

## 5. TraderService.cs

**Розташування:** `Services/TraderService.cs`
**Успадковує:** `PythonRunnerBase`
**Реалізує:** `ITrader`
**Роль:** Головний сервіс торгівлі. Всі операції виконує через `cs_bridge.py`.

### Конструктор

```csharp
public TraderService(string pythonExe, string scriptsFolder)
    : base(pythonExe, scriptsFolder)  // передаємо батьку
{
    _bridge = Path.Combine(scriptsFolder, "cs_bridge.py");
}
```

`: base(...)` — виклик конструктора батьківського класу `PythonRunnerBase`.
`_bridge` — повний шлях до `cs_bridge.py`, який зберігається одразу.

### OpenTrade — відкриття позиції

```csharp
public (bool success, string message) OpenTrade(TradeInfo trade)
```

**Послідовність дій:**

**Крок 1 — локальна перевірка RR:**
```csharp
var (rrOk, rrMsg) = CheckRR(trade);
if (!rrOk) return (false, rrMsg);
```
Перевіряємо RR локально в C# (без Python) Якщо RR < 2.0 — відразу повертаємо помилку.

**Крок 2 — розрахунок плеча через Python:**
```csharp
int leverage = CalcLeverage(trade);
trade.Leverage = leverage;
```
Викликає `cs_bridge.py calc_leverage` який запускає `leverage.py`.
`leverage.py` отримує реальний баланс з Binance і рахує оптимальне плече.

**Крок 3 — відкриття позиції:**
```csharp
string json = BuildJson(new { pair, direction, entry, stop, ... });
var (ok, data, error) = CallBridge("open_trade", json);
```
Формує JSON і викликає `cs_bridge.py open_trade`. Той запускає
`Trader.open_trade()` який ставить реальні ордери на Binance.

**Крок 4 — подія:**
```csharp
if (ok) OnTradeOpened?.Invoke(trade);
```
Якщо все успішно — стріляє подією. Form1 підписана на цю подію
і виведе `🟢 Відкрито: BTCUSDT long | RR 3.45` в лог.

### CallBridge — центральний метод виклику Python

```csharp
private (bool ok, dynamic data, string error) CallBridge(string action, string jsonArgs)
```

Це найважливіший приватний метод. Він:
1. Перевіряє чи існує `cs_bridge.py`
2. Екранує JSON для передачі як аргумент командного рядка
3. Викликає `RunScript` (успадкований від батька)
4. Парсить JSON відповідь

**Складний момент — екранування JSON:**
```csharp
string safeJson = jsonArgs.Replace("\"", "\\\"");
string output   = RunScript(_bridge, $"{action} \"{safeJson}\"");
```
JSON містить лапки `"`. Щоб передати їх як аргумент командного рядка,
треба екранувати: `"` → `\"`. Інакше Windows CMD вирішить що аргумент
завершився і решта JSON буде втрачена.

**Складний момент — `dynamic` та парсинг останнього рядка:**
```csharp
string lastLine = output.Trim().Split('\n')[^1].Trim();
dynamic result  = Newtonsoft.Json.JsonConvert.DeserializeObject(lastLine);
```
`[^1]` — індексація з кінця (C# 8+), `[^1]` = останній елемент.
Беремо останній рядок бо Python може виводити warnings перед JSON
(наприклад застаріла версія бібліотеки, або FutureWarning від pandas).
`dynamic` — тип який дозволяє звертатись до полів без компіляційної
перевірки: `result.ok`, `result.data.leverage` і т.д.

### CheckRR — локальна перевірка RR

```csharp
private (bool ok, string message) CheckRR(TradeInfo t)
```

Дзеркалить логіку `checks.py` але на C# — без запуску Python.
Перевіряє що для Long: `stop < entry < take`,
для Short: `take < entry < stop`.
Мінімальний RR = 2.0 (як в оригінальному `checks.py`).

### FallbackLeverage — запасний розрахунок плеча

```csharp
private int FallbackLeverage(TradeInfo trade)
{
    double stopPct = Math.Abs((double)(trade.EntryPrice - trade.StopLoss)
                     / (double)trade.EntryPrice);
    int lev = (int)Math.Floor((double)trade.RiskPercent / 100.0 / stopPct);
    return Math.Max(1, Math.Min(lev, 125));
}
```

Якщо Python не зміг порахувати плече (немає з'єднання, помилка) —
використовується проста формула: `leverage = risk% / stop%`.
`Math.Max(1, Math.Min(lev, 125))` — обмежуємо в діапазоні [1, 125].

---

## 6. MonitorService.cs

**Розташування:** `Services/MonitorService.cs`
**Успадковує:** `PythonRunnerBase`
**Реалізує:** `IMonitor`
**Роль:** Тримає два таймери — один для балансу, другий для позицій.

### Два таймери

```csharp
private readonly System.Windows.Forms.Timer _balanceTimer;  // кожні 10 сек
private readonly System.Windows.Forms.Timer _monitorTimer;  // кожні 3 сек (вручну)
```

Чому `System.Windows.Forms.Timer` а не просто `Timer`?
Бо .NET має кілька класів `Timer` в різних просторах імен:
- `System.Windows.Forms.Timer` — спрацьовує в UI потоці (безпечно для UI)
- `System.Threading.Timer` — спрацьовує в потоці пулу (треба Invoke для UI)
- `System.Timers.Timer` — теж не в UI потоці

Ми використовуємо `WinForms.Timer` бо він автоматично працює в UI потоці
і не потребує `InvokeRequired`.

### GetBalance — отримання балансу

```csharp
public BalanceInfo GetBalance()
{
    string output = RunScript(_bridge, "get_balance \"{}\"");
    return ParseBridgeBalance(output);
}
```

Викликає `cs_bridge.py get_balance` → той запускає `parcer.py` →
`parcer.py` звертається до Binance API → повертає JSON з балансом.

### ParseBridgeBalance — парсинг відповіді

```csharp
return new BalanceInfo
{
    Total       = (decimal)(double)result.data.total,
    Available   = (decimal)(double)result.data.available,
    InPositions = (decimal)(double)result.data.used
};
```

**Чому подвійне приведення `(decimal)(double)`?**
`dynamic` від Newtonsoft.Json повертає числа як `double` (64-bit float).
Напряму конвертувати `dynamic` → `decimal` не можна — компілятор не знає
точний тип під час компіляції. Тому: спочатку явно в `double`, потім в `decimal`.

### Dispose — звільнення ресурсів

```csharp
public void Dispose()
{
    _balanceTimer?.Stop();
    _balanceTimer?.Dispose();
    _monitorTimer?.Stop();
    _monitorTimer?.Dispose();
}
```

`Form1.cs` викликає `Dispose()` при закритті вікна. Таймери — це системні
ресурси, їх треба явно звільняти інакше вони продовжать тікати навіть
після закриття форми і викличуть помилки.

---

## 7. FreqtradeService.cs

**Розташування:** `Services/FreqtradeService.cs`
**Успадковує:** `PythonRunnerBase`
**Роль:** Запускає Freqtrade Streamlit у окремому терміналі і відкриває браузер.

### Launch — запуск Streamlit

```csharp
public void Launch()
{
    // Перевіряємо файли
    if (!File.Exists(_interfacePath)) { Log("❌ Interface.py не знайдено"); return; }
    if (!IsPythonAvailable())         { Log("❌ Python не знайдено"); return; }

    var psi = new ProcessStartInfo
    {
        FileName  = PythonExePath,
        Arguments = $"-m streamlit run \"{_interfacePath}\" --server.port={_port}",
        UseShellExecute = true,   // новий термінал
    };

    Process.Start(psi);
    Log($"✅ Freqtrade запущено на порті {_port}");

    // Відкриваємо браузер через 4 секунди (Streamlit потребує час на старт)
    var timer = new System.Windows.Forms.Timer { Interval = 4000 };
    timer.Tick += (_, __) =>
    {
        Process.Start(new ProcessStartInfo
        {
            FileName        = $"http://localhost:{_port}",
            UseShellExecute = true   // відкриває браузер за замовчуванням
        });
        timer.Stop();
        timer.Dispose();  // таймер одноразовий — відразу видаляємо
    };
    timer.Start();
}
```

**Лямбда в Tick:**
```csharp
timer.Tick += (_, __) => { ... };
```
`_` і `__` — це параметри `sender` і `EventArgs` які нам не потрібні.
За конвенцією непотрібні параметри позначають `_`.

---

## 8. Form1.Designer.cs

**Розташування:** `Forms/Form1.Designer.cs`
**Роль:** Автогенерований файл розмітки UI. Визначає де і як
розташовані всі елементи головного вікна.

### partial class

```csharp
// Form1.Designer.cs
public partial class Form1 : Form { ... }

// Form1.cs
public partial class Form1 : Form { ... }
```

`partial` дозволяє розбити один клас на кілька файлів.
При компіляції C# склеює їх в один клас. WinForms завжди використовує
цей підхід: Designer генерує UI-код окремо від логіки.

### Хелпери для коротшого запису

```csharp
private System.Windows.Forms.Label MakeLabel(string text, int x, int y) { ... }
private System.Windows.Forms.TextBox MakeTextBox(int x, int y, string text = "") { ... }
private System.Windows.Forms.ComboBox MakeCombo(int x, int y, string[] items, bool editable) { ... }
private System.Windows.Forms.Button MakeButton(string text, int x, int y, Color color) { ... }
```

Замість того щоб кожен раз писати 10 рядків для кожного контрола,
ми зробили хелпери. Кожен хелпер створює контрол з типовими
темними налаштуваннями (BackColor, ForeColor, Font).

### Підписка на події кнопок

```csharp
this.btnOpenPosition.Click += new System.EventHandler(this.btnOpenPosition_Click);
```

Ось де кнопки "підключаються" до обробників в `Form1.cs`.
Без цього рядка кнопка існує у вікні але нічого не робить при кліку.

### Anchor — динамічний розмір панелі логу

```csharp
this.pnlLog.Anchor = AnchorStyles.Top | AnchorStyles.Bottom
                   | AnchorStyles.Right;
```

`Anchor` означає: при зміні розміру вікна, цей контрол "прилипає"
до вказаних сторін і розтягується разом з вікном.
`Top | Bottom | Right` — панель логу завжди займає повну висоту
і притиснута до правого краю.

---

## 9. Form1.cs

**Розташування:** `Forms/Form1.cs`
**Роль:** Серце програми. З'єднує UI з сервісами, обробляє всі події.

### Поля — конкретні типи замість інтерфейсів

```csharp
private TraderService    _trader;
private MonitorService   _monitor;
private FreqtradeService _freqtrade;
```

Зверни увагу — не `ITrader _trader` а `TraderService _trader`.
Чому? Бо `OnLog` подія є в `PythonRunnerBase` (батьківський клас),
а не в інтерфейсі `ITrader`. Через інтерфейс до `OnLog` не дістатись.

### SCRIPTS_FOLDER — динамічний шлях

```csharp
private static readonly string SCRIPTS_FOLDER =
    Path.GetFullPath(Path.Combine(
        AppDomain.CurrentDomain.BaseDirectory, @"..\..\..\..\"));
```

`AppDomain.CurrentDomain.BaseDirectory` — папка де знаходиться `.exe`.
При `dotnet run` це: `HighTechTrader\bin\Debug\net10.0-windows\`

Піднімаємось на 4 рівні вгору:
```
bin\Debug\net10.0-windows\  →  ..\
HighTechTrader\bin\Debug\   →  ..\
HighTechTrader\bin\         →  ..\
HighTechTrader\             →  ..\
Traid_Platform\             ← тут лежать .py файли ✅
```

`Path.GetFullPath` нормалізує шлях — прибирає `..` і робить його абсолютним.

### BindEvents — підписка на події сервісів

```csharp
private void BindEvents()
{
    _trader.OnLog    += msg => Log(msg, Color.FromArgb(0, 220, 180));
    _monitor.OnLog   += msg => Log(msg, Color.Gray);
    _freqtrade.OnLog += msg => Log(msg, Color.FromArgb(100, 180, 255));

    _monitor.OnBalanceUpdated += OnBalanceUpdated;
    _trader.OnTradeOpened     += trade => Log($"🟢 Відкрито: {trade.Pair}", Color.Green);
    _trader.OnTradeClosed     += (pair, reason) => Log($"🔴 Закрито: {pair}", Color.Red);
}
```

Кожен сервіс має свій колір логів — одразу видно звідки прийшло
повідомлення. Лямбди `msg => Log(...)` — короткий запис анонімної функції.

### Log — кольоровий вивід в RichTextBox

```csharp
private void Log(string message, Color color)
{
    if (InvokeRequired)
    {
        Invoke(new Action(() => Log(message, color)));
        return;
    }

    Console.WriteLine(message);                        // термінал

    string line = $"[{DateTime.Now:HH:mm:ss}] {message}";
    rtbLog.SelectionStart  = rtbLog.TextLength;
    rtbLog.SelectionLength = 0;
    rtbLog.SelectionColor  = color;
    rtbLog.AppendText(line + Environment.NewLine);
    rtbLog.SelectionColor  = rtbLog.ForeColor;        // скидаємо колір
    rtbLog.ScrollToCaret();                            // автоскрол вниз
}
```

**`InvokeRequired` — потокова безпека:**
Таймери і події від сервісів можуть спрацювати в будь-якому потоці.
WinForms дозволяє змінювати UI **тільки з UI-потоку**.
`InvokeRequired == true` означає "ми в чужому потоці".
`Invoke(...)` передає виклик в UI-поток і ми рекурсивно викликаємо
`Log` вже з правильного потоку.

**Вибіркове забарвлення в RichTextBox:**
```csharp
rtbLog.SelectionStart  = rtbLog.TextLength;  // курсор в кінець
rtbLog.SelectionLength = 0;                  // нічого не виділено
rtbLog.SelectionColor  = color;              // наступний текст — цим кольором
rtbLog.AppendText(line + "\n");
rtbLog.SelectionColor  = rtbLog.ForeColor;   // скидаємо до дефолту
```
`RichTextBox` дозволяє кожному рядку мати свій колір через
маніпуляцію `SelectionColor` перед `AppendText`.

### TryReadInputs — читання і валідація полів

```csharp
private bool TryReadInputs(out TradeInfo trade)
```

`out` параметр — C# спосіб повернути кілька значень.
Функція повертає `bool` (успіх) і через `out` передає `TradeInfo`.

```csharp
private decimal ParseDecimal(string s)
    => decimal.Parse(s.Trim().Replace(",", "."),
        System.Globalization.CultureInfo.InvariantCulture);
```

`Replace(",", ".")` — користувач може ввести `0,2759` замість `0.2759`.
`InvariantCulture` — незалежно від мови системи завжди використовує `.`
як десятковий роздільник.

---

## 10. OpenTradeDialog.cs

**Розташування:** `Forms/OpenTradeDialog.cs`
**Успадковує:** `Form`
**Роль:** Показує деталі угоди до підтвердження. Містить поля
для журналу трейдера (причина входу, Fear&Greed і т.д.).

### Конструктор і послідовність ініціалізації

```csharp
public OpenTradeDialog(TradeInfo trade)
{
    _trade = trade;
    CalculateRR();       // 1. Рахуємо RR з наданих цін
    InitializeComponent(); // 2. Створюємо контроли
    PopulateInfo();       // 3. Заповнюємо контроли даними
}
```

Важливо що `CalculateRR()` іде **до** `InitializeComponent()`.
Якби ми поміняли місцями — в `PopulateInfo` ми б звертались до
контролів які ще не створені і отримали б `NullReferenceException`.

### ValidateDelegate — зовнішня валідація

```csharp
[DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
public Func<TradeInfo, (bool ok, string msg)> ValidateDelegate { get; set; }
```

`Func<TradeInfo, (bool ok, string msg)>` — тип делегата: функція що
приймає `TradeInfo` і повертає tuple з bool і string.

`[DesignerSerializationVisibility(Hidden)]` — атрибут що забороняє
WinForms Designer намагатись серіалізувати цю властивість.
Без нього — помилка `WFO1000` при компіляції.

`Form1.cs` встановлює цей делегат перед показом діалогу:
```csharp
dlg.ValidateDelegate = t =>
{
    bool ok = t.RR >= 1.5;
    return (ok, $"RR {t.RR:F2} < 1.5");
};
```

### AddLabel і AddInfoRow — хелпери для UI

```csharp
private Label AddLabel(string text, int x, int y, int w, int h,
    float fontSize = 10F, bool bold = false, Color? color = null)
```

`Color? color = null` — nullable тип. `?` після типу означає що
значення може бути `null`. Якщо не передали колір — використовуємо дефолтний.

```csharp
ForeColor = color ?? Color.FromArgb(0, 255, 170),
```
`??` — null-coalescing оператор: якщо `color` є null → використай праву частину.

### get_data через ResultTrade

```csharp
public TradeInfo ResultTrade => _trade;
```

`=>` без тіла методу — це expression-bodied property (властивість-вираз).
Еквівалентно:
```csharp
public TradeInfo ResultTrade { get { return _trade; } }
```

Після `dlg.ShowDialog() == DialogResult.OK` Form1 читає:
```csharp
var (success, msg) = _trader.OpenTrade(dlg.ResultTrade);
```

---

## 11. CloseTradeDialog.cs

**Розташування:** `Forms/CloseTradeDialog.cs`
**Успадковує:** `Form`
**Роль:** Простий діалог — список відкритих позицій і поле для причини закриття.

### Властивості з ініціалізатором

```csharp
public string SelectedPair { get; private set; } = string.Empty;
public string CloseReason  { get; private set; } = string.Empty;
```

`= string.Empty` — ініціалізуємо порожнім рядком замість `null`.
`private set` — можна читати ззовні, але змінювати тільки зсередини класу.

### Отримання пари з позиції

```csharp
SelectedPair = cmbPositions.SelectedItem.ToString()?.Split(' ')[0] ?? string.Empty;
```

Позиція виглядає як `"BTCUSDT (LONG)"`.
`Split(' ')[0]` → `"BTCUSDT"` — беремо тільки назву пари.
`?.` — якщо `ToString()` поверне null (не може але компілятор перестраховується).
`?? string.Empty` — якщо результат null → порожній рядок.

---

## 12. cs_bridge.py

**Розташування:** `Traid_Platform\cs_bridge.py` (поруч з іншими .py)
**Роль:** Єдина точка входу з C# у всі Python модулі.

### Чому потрібен bridge?

`trader.py` — це клас `Trader` з методами. Він не CLI скрипт і не приймає
аргументи командного рядка. `parcer.py`, `leverage.py` — теж функції, не CLI.

C# може викликати Python тільки через `Process.Start` передаючи аргументи.
`cs_bridge.py` перетворює CLI виклик в виклики Python функцій:

```
C# викликає:
  python.exe cs_bridge.py open_trade "{\"pair\":\"BTCUSDT\",\"entry\":94000,...}"

cs_bridge.py робить:
  from trader import Trader
  t = Trader()
  ok, msg = t.open_trade(pair="BTCUSDT", entry=94000, ...)
  print(json.dumps({"ok": ok, "data": {"message": msg}, "error": ""}))
```

### Формат відповіді — завжди JSON

```python
def respond(ok: bool, data=None, error: str = ""):
    result = {"ok": ok, "data": data, "error": error}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if ok else 1)
```

`ensure_ascii=False` — дозволяє виводити кирилицю і emoji напряму.
`sys.exit(0)` при успіху, `sys.exit(1)` при помилці.

### UTF-8 fix

```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
```

`hasattr` — перевіряємо чи метод існує (в старих Python < 3.7 його нема).
Це парна частина до `StandardOutputEncoding = Encoding.UTF8` в C#.

---

## 13. Схема взаємодії між файлами

```
┌─────────────────────────────────────────────────────────────────┐
│                         WINFORMS UI                             │
│                                                                 │
│  Form1.Designer.cs ──────► Form1.cs                            │
│  (розмітка кнопок)         (обробники кліків)                  │
│                               │                                 │
│              ┌────────────────┼─────────────────┐              │
│              │                │                 │              │
│              ▼                ▼                 ▼              │
│  OpenTradeDialog    CloseTradeDialog    lblFooter/rtbLog       │
└──────────────┼────────────────┼─────────────────────────────────┘
               │                │
               ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SERVICES                                │
│                                                                 │
│  PythonRunnerBase (abstract)                                    │
│       │                                                         │
│       ├──► TraderService   ──► OpenTrade / CloseTrade          │
│       │         │               GetPositions / Monitor         │
│       │         │                                              │
│       ├──► MonitorService ──► GetBalance (таймер 10сек)        │
│       │         │               RefreshPositions (таймер 3сек) │
│       │                                                         │
│       └──► FreqtradeService ──► Launch (Streamlit)             │
└─────────────────┼───────────────────────────────────────────────┘
                  │  Process.Start (stdout/stdin)
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      cs_bridge.py                               │
│                                                                 │
│  get_balance   ──► parcer.py   ──► Binance API                 │
│  calc_leverage ──► leverage.py ──► parcer.py ──► Binance API   │
│  open_trade    ──► trader.py   ──► checks.py                   │
│                                    leverage.py                  │
│                                    database.py                  │
│                                    Binance API                  │
│  close_trade   ──► trader.py   ──► Binance API                 │
│  get_positions ──► trader.py   ──► Binance API                 │
│  monitor       ──► trader.py   ──► Binance API                 │
└─────────────────────────────────────────────────────────────────┘

Події (стрілки знизу вгору):
  TraderService.OnLog          ──► Form1.Log()  (кожне повідомлення)
  TraderService.OnTradeOpened  ──► Form1.Log()  (після відкриття)
  TraderService.OnTradeClosed  ──► Form1.Log()  (після закриття)
  MonitorService.OnLog         ──► Form1.Log()  (кожне повідомлення)
  MonitorService.OnBalanceUpdated ──► Form1.OnBalanceUpdated() (баланс)
```

---

## 14. Складні моменти коду

### 14.1 Чому `(bool success, string message)` а не `bool`?

```csharp
public (bool success, string message) OpenTrade(TradeInfo trade)
```

Це tuple — кортеж. Дозволяє повернути кілька значень без окремого класу.
Альтернатива — `out` параметр або окремий клас `TradeResult`.
Tuple зручніший для простих випадків:

```csharp
var (ok, msg) = _trader.OpenTrade(trade);  // деструктуризація
if (ok) Log(msg, Color.Green);
else    Log(msg, Color.Red);
```

### 14.2 Чому `dynamic` в CallBridge?

```csharp
dynamic result = Newtonsoft.Json.JsonConvert.DeserializeObject(lastLine);
bool ok = (bool)result.ok;
```

JSON має невідому нам структуру під час компіляції.
`dynamic` відкладає перевірку типів на час виконання.
Альтернатива — `JObject` від Newtonsoft:

```csharp
var result = JObject.Parse(lastLine);
bool ok = result["ok"].Value<bool>();
```

Обидва підходи працюють, `dynamic` коротший.

### 14.3 Чому `[^1]` для останнього рядка?

```csharp
string lastLine = output.Trim().Split('\n')[^1].Trim();
```

`[^1]` — індекс з кінця (C# 8, .NET 3+).
`[^1]` = `[array.Length - 1]` = останній елемент.
Беремо останній рядок бо Python може друкувати попередження
перед JSON відповіддю. Ми знаємо що `respond()` в bridge завжди
пише JSON останнім рядком.

### 14.4 EnvironmentVariables і UseShellExecute

```csharp
psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
// Але тільки якщо UseShellExecute = false!
```

`EnvironmentVariables` не працює разом з `UseShellExecute = true`.
Коли `UseShellExecute = true` — Windows Shell запускає процес і
не передає наші змінні середовища. Тому:
- `RunScript` → `UseShellExecute = false` → можна задавати ENV
- `RunScriptAsync` → `UseShellExecute = true` → не можна задавати ENV (і не треба, бо не читаємо stdout)

### 14.5 Dispose і IDisposable

```csharp
// Form1.cs
protected override void OnFormClosing(FormClosingEventArgs e)
{
    _monitor?.StopMonitoring();
    _monitor?.Dispose();
    base.OnFormClosing(e);
}
```

`?.` — якщо `_monitor` є null (ініціалізація не завершилась через помилку)
— не впаде з NullReferenceException.

`Dispose()` зупиняє таймери. Якщо не викликати — таймери продовжать
тікати після закриття форми, будуть запускати Python процеси
і програма не завершиться коректно.

`base.OnFormClosing(e)` — **обов'язково** викликати батьківський метод,
інакше вікно не закриється (WinForms обробляє закриття у базовому класі).

### 14.6 using var для діалогів

```csharp
using var dlg = new OpenTradeDialog(trade);
if (dlg.ShowDialog() == DialogResult.OK) { ... }
// тут автоматично викликається dlg.Dispose()
```

`using var` — після виходу з блоку автоматично викликає `Dispose()`.
Форми зберігають GDI ресурси (шрифти, пензлі). `Dispose()` їх звільняє.
Без `using` — витік пам'яті при частому відкритті/закритті діалогів.