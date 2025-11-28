"""
Dio 配置生成器

生成 Dio 配置代码
"""
from typing import Optional


class DioConfigGenerator:
    """生成 Dio 配置代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Flutter 项目的基础包名
        """
        self.base_package = base_package
    
    def generate_config(
        self,
        base_url: str = "https://api.example.com",
        timeout_seconds: int = 30,
        enable_logging: bool = True
    ) -> str:
        """
        生成 Dio 配置代码
        
        Args:
            base_url: API 基础 URL
            timeout_seconds: 超时时间（秒）
            enable_logging: 是否启用日志拦截器
        
        Returns:
            生成的 Dart 代码字符串
        """
        lines = [
            "import 'package:dio/dio.dart';",
            "import 'package:dio/io.dart';",
            "import '../services/api_service.dart';",
            "",
            "/// Dio 配置类",
            "/// 自动生成的配置文件",
            "/// 由 ShowDoc 文档自动生成",
            "class DioConfig {",
            "",
            f"  static const String baseUrl = '{base_url}';",
            f"  static const int timeoutSeconds = {timeout_seconds};",
            "",
            "  /// 创建 Dio 实例",
            "  static Dio createDio() {",
            "    final dio = Dio(BaseOptions(",
            "      baseUrl: baseUrl,",
            "      connectTimeout: Duration(seconds: timeoutSeconds),",
            "      receiveTimeout: Duration(seconds: timeoutSeconds),",
            "      sendTimeout: Duration(seconds: timeoutSeconds),",
            "    ));",
            "",
        ]
        
        if enable_logging:
            lines.extend([
                "    // 添加日志拦截器（仅在 Debug 模式下）",
                "    // 注意：需要添加 dio_logging_interceptor 依赖",
                "    // dio.interceptors.add(LogInterceptor(",
                "    //   requestBody: true,",
                "    //   responseBody: true,",
                "    // ));",
                "",
            ])
        
        lines.extend([
            "    // TODO: 根据需要添加其他拦截器",
            "    // 例如：认证拦截器、错误处理拦截器等",
            "",
            "    return dio;",
            "  }",
            "",
            "  /// 创建 ApiService 实例",
            "  /// 注意：需要实现 ApiService 抽象类",
            "  /// 例如：",
            "  /// class ApiServiceImpl extends ApiService {",
            "  ///   ApiServiceImpl(super.dio);",
            "  /// }",
            "  static ApiService createApiService() {",
            "    // TODO: 实现 ApiService 的具体类",
            "    throw UnimplementedError('需要实现 ApiService 的具体类');",
            "  }",
            "",
            "}",
        ])
        
        return "\n".join(lines)

