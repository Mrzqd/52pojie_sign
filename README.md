# 2024/8/22
修复了52破解的签到，此版本需要填写PJ52_TOKEN环境变量，具体请参考tg群聊。
# 现在不能签到的我也无能为力了，目前来看吾爱新增了一个加密的请求，这个请求根据申请任务返回的wzws_sid，去生成一个字符串，看着像RSA加密了一个字符串后的内容，用这个加密的字符串请求waf_zw_verify接口验证后返回新的wzws_sid，新的wzws_sid就可以用来签到。由于吾爱开启了反debug,我也找不出加密方式和公钥。那个加密用的js还是加密混淆的。就挺离谱！
# 国内云服务器用户请使用代理（国内云服务ip已被吾爱拉黑，无法签到）
# 国外云服务器无法完成MT论坛签到
# 52pojie_sign
吾爱破解签到脚本
# 如果您感觉有用请您为本项目点个star
# 第一步获取吾爱cookie
![image](https://user-images.githubusercontent.com/104408988/215322514-71589c11-1454-4db1-acf5-3d0066c8334b.png)
# 第二步
将获取到的cookie填写进脚本的cookies = ""的引号里；
本地运行，青龙(青龙可以在环境变量添加PJ52_COOKIE，多账户直接添加多个PJ52_COOKIE即可)运行均可（需要requests和bs4依赖）
# 如有疑问请加TG群https://t.me/+gv73-FuXRP0xZTA1
# 有疑问就上tg问吧，issues交流太麻烦了，issues就关了
------------------------------------------------------
# 新增阿里网盘签到
参考了([ImYrS/aliyun-auto-signin](https://github.com/ImYrS/aliyun-auto-signin))大佬的项目，感谢！
# 使用方法
首次运行会生成aliwangpan.json配置文件，将自己获取的refresh_token填入，并将is的值修改为1即可！
| 功能   | 是否支持 |
|------|:----:|
| 签到   |  Y   |
| 多账户  |  Y   |

[![Powered by DartNode](https://dartnode.com/branding/DN-Open-Source-sm.png)](https://dartnode.com "Powered by DartNode - Free VPS for Open Source")
