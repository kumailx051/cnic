# Azure Deployment Configuration
web.config:
```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="D:\home\python364x64\python.exe"
                  arguments="D:\home\site\wwwroot\main.py"
                  stdoutLogEnabled="true"
                  stdoutLogFile="D:\home\LogFiles\python.log"
                  startupTimeLimit="60"
                  requestTimeout="00:04:00">
      <environmentVariables>
        <environmentVariable name="PORT" value="%HTTP_PLATFORM_PORT%" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
```

app_settings.json:
```json
{
    "FLASK_ENV": "production",
    "PYTHONPATH": "/home/site/wwwroot",
    "SCM_DO_BUILD_DURING_DEPLOYMENT": "true"
}
```
