Set shell = CreateObject("WScript.Shell")
here = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = here
If WScript.Arguments.Count > 0 Then WScript.Sleep 10000
shell.Run """" & here & "\venv\Scripts\pythonw.exe"" avatar.py", 0, False