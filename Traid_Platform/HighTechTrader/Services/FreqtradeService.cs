using System;
using System.Diagnostics;
using System.IO;

namespace HighTechTrader
{
    /// <summary>
    /// Запуск Freqtrade Streamlit Interface.py
    /// Успадковує PythonRunnerBase, перевизначає RunScriptAsync для streamlit
    /// </summary>
    public class FreqtradeService : PythonRunnerBase
    {
        private readonly string _freqtradeFolder;
        private readonly string _interfacePath;
        private readonly int    _port;

        public FreqtradeService(string freqtradeFolder, int port = 8501)
            : base(
                Path.Combine(freqtradeFolder, ".venv", "Scripts", "python.exe"),
                freqtradeFolder)
        {
            _freqtradeFolder = freqtradeFolder;
            _interfacePath   = Path.Combine(freqtradeFolder, "Interface.py");
            _port            = port;
        }

        /// <summary>
        /// Запускає Streamlit у новому терміналі, потім відкриває браузер
        /// </summary>
        public void Launch()
        {
            if (!File.Exists(_interfacePath))
            {
                Log($"❌ Interface.py не знайдено: {_interfacePath}");
                return;
            }
            if (!IsPythonAvailable())
            {
                Log($"❌ Python не знайдено: {PythonExePath}");
                return;
            }

            var psi = new ProcessStartInfo
            {
                FileName  = PythonExePath,
                Arguments = $"-m streamlit run \"{_interfacePath}\" " +
                            $"--server.port={_port} --server.headless=false",
                WorkingDirectory  = _freqtradeFolder,
                UseShellExecute   = true,        // відкриває нове вікно консолі
                CreateNoWindow    = false,
            };

            try
            {
                Process.Start(psi);
                Log($"✅ Freqtrade Streamlit запущено на порті {_port}");

                // Відкриваємо браузер через 4 секунди
                var timer = new System.Windows.Forms.Timer { Interval = 4000 };
                timer.Tick += (_, __) =>
                {
                    System.Diagnostics.Process.Start(new ProcessStartInfo
                    {
                        FileName        = $"http://localhost:{_port}",
                        UseShellExecute = true
                    });
                    timer.Stop();
                    timer.Dispose();
                };
                timer.Start();
            }
            catch (Exception ex)
            {
                Log($"❌ Freqtrade: {ex.Message}");
            }
        }
    }
}