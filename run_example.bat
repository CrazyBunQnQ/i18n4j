@echo off
chcp 65001 >nul
echo ====================================
echo Java Spring Boot 国际化字符串提取工具
echo ====================================
echo.
echo 使用方法:
echo python i18n_extractor.py ^<项目目录^> ^<配置文件路径^>
echo.
echo 示例:
echo python i18n_extractor.py C:\path\to\spring-project C:\path\to\messages.properties
echo.
echo 运行测试示例:
echo python test_example.py
echo.
echo 按任意键运行测试示例...
pause >nul
echo.
echo 正在运行测试示例...
python test_example.py
echo.
echo 测试完成！
pause