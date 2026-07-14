using System;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace HighTechTrader
{
    /// <summary>
    /// Базовий клас для запуску Python-скриптів через Process.Start
    /// Всі сервіси успадковують цей клас
    /// </summary>
    public abstract class PythonRunnerBase : IPythonRunner
    {
        // Конфігурація 
        protected readonly string PythonExePath;
        protected readonly string ScriptsFolder;

        //Подія логування (делегат LogEventHandler)
        public event LogEventHandler OnLog;

        protected PythonRunnerBase(string pythonExePath, string scriptsFolder)
        {
            PythonExePath = pythonExePath ?? FindPythonExe();
            ScriptsFolder = scriptsFolder ?? AppDomain.CurrentDomain.BaseDirectory;
        }

        // IPythonRunner

        /// <summary>
        /// Синхронний запуск .py скрипта, повертає stdout
        /// </summary>
        public virtual string RunScript(string scriptPath, string arguments = "")
        {
            if (!File.Exists(scriptPath))
            {
                Log($"❌ Скрипт не знайдено: {scriptPath}");
                return null;
            }

            var psi = BuildProcessInfo(scriptPath, arguments);
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardError  = true;
            psi.UseShellExecute        = false;
            psi.CreateNoWindow         = true;

            var sb = new StringBuilder();
            try
            {
                using var proc = Process.Start(psi) ?? throw new InvalidOperationException("Не вдалось запустити процес");
                string output = proc.StandardOutput.ReadToEnd();
                string error  = proc.StandardError.ReadToEnd();
                proc.WaitForExit();

                if (!string.IsNullOrWhiteSpace(output))
                {
                    sb.Append(output);
                    Log($"[py stdout] {output.Trim()}");
                }
                if (!string.IsNullOrWhiteSpace(error))
                {
                    Log($"⚠️ [py stderr] {error.Trim()}");
                }

                return sb.ToString().Trim();
            }
            catch (Exception ex)
            {
                Log($"❌ Помилка запуску Python: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Асинхронний запуск — відкриває новий термінал
        /// </summary>
        public virtual void RunScriptAsync(string scriptPath, string arguments = "")
        {
            if (!File.Exists(scriptPath))
            {
                Log($"❌ Скрипт не знайдено: {scriptPath}");
                return;
            }

            var psi = BuildProcessInfo(scriptPath, arguments);
            psi.UseShellExecute = true;  // нова консоль

            try
            {
                Process.Start(psi);
                Log($"✅ Запущено: {Path.GetFileName(scriptPath)}");
            }
            catch (Exception ex)
            {
                Log($"❌ {ex.Message}");
            }
        }

        public bool IsPythonAvailable()
        {
            return File.Exists(PythonExePath);
        }

        //Захищені допоміжні методи

        protected ProcessStartInfo BuildProcessInfo(string scriptPath, string arguments)
        {
            return new ProcessStartInfo
            {
                FileName = PythonExePath,
                Arguments = $"\"{scriptPath}\" {arguments}",
                CreateNoWindow = false,
                WorkingDirectory = ScriptsFolder,
            };
        }

        /// <summary>
        /// Надсилає подію логу — використовується нащадками
        /// </summary>
        protected void Log(string message)
        {
            OnLog?.Invoke($"[{DateTime.Now:HH:mm:ss}] {message}");
        }

        // Пошук python.exe якщо шлях не заданий
        private static string FindPythonExe()
        {
            // Шукаємо спочатку venv у тій же теці
            string venv = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, ".venv", "Scripts", "python.exe");
            if (File.Exists(venv)) return venv;

            // Потім у PATH
            return "python.exe";
        }
    }
}