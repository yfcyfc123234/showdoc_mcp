"""
OkHttp 配置生成器

生成 OkHttp 和 Retrofit 配置代码
"""
from typing import Optional


class OkHttpConfigGenerator:
    """生成 OkHttp 和 Retrofit 配置代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Android 项目的基础包名
        """
        self.base_package = base_package
    
    def generate_config(
        self,
        base_url: str = "https://api.example.com",
        timeout_seconds: int = 30,
        enable_logging: bool = True
    ) -> str:
        """
        生成 OkHttp 和 Retrofit 配置代码
        
        Args:
            base_url: API 基础 URL
            timeout_seconds: 超时时间（秒）
            enable_logging: 是否启用日志拦截器
        
        Returns:
            生成的 Kotlin 代码字符串
        """
        lines = [
            f"package {self.base_package}.config",
            "",
            "import okhttp3.OkHttpClient",
            "import okhttp3.logging.HttpLoggingInterceptor",
            "import retrofit2.Retrofit",
            "import retrofit2.converter.gson.GsonConverterFactory",
            "import java.util.concurrent.TimeUnit",
            f"import {self.base_package}.services.ApiService",
            "",
            "/**",
            " * OkHttp 和 Retrofit 配置",
            " * 自动生成的配置文件",
            " * 由 ShowDoc 文档自动生成",
            " */",
            "object OkHttpConfig {",
            "",
            f"    private const val BASE_URL = \"{base_url}\"",
            f"    private const val TIMEOUT_SECONDS = {timeout_seconds}L",
            "",
            "    /**",
            "     * 创建 OkHttpClient",
            "     */",
            "    fun createOkHttpClient(): OkHttpClient {",
            "        val builder = OkHttpClient.Builder()",
            "",
            f"        // 设置超时时间",
            "        builder.connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)",
            "        builder.readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)",
            "        builder.writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)",
            "",
        ]
        
        if enable_logging:
            lines.extend([
                "        // 添加日志拦截器（仅在 Debug 模式下）",
                "        if (BuildConfig.DEBUG) {",
                "            val loggingInterceptor = HttpLoggingInterceptor().apply {",
                "                level = HttpLoggingInterceptor.Level.BODY",
                "            }",
                "            builder.addInterceptor(loggingInterceptor)",
                "        }",
                "",
            ])
        
        lines.extend([
            "        // TODO: 根据需要添加其他拦截器",
            "        // 例如：认证拦截器、错误处理拦截器等",
            "",
            "        return builder.build()",
            "    }",
            "",
            "    /**",
            "     * 创建 Retrofit 实例",
            "     */",
            "    fun createRetrofit(): Retrofit {",
            "        return Retrofit.Builder()",
            "            .baseUrl(BASE_URL)",
            "            .client(createOkHttpClient())",
            "            .addConverterFactory(GsonConverterFactory.create())",
            "            .build()",
            "    }",
            "",
            "    /**",
            "     * 创建 ApiService 实例",
            "     */",
            "    fun createApiService(): ApiService {",
            "        return createRetrofit().create(ApiService::class.java)",
            "    }",
            "",
            "}",
        ])
        
        return "\n".join(lines)
    
    def generate_dependency_injection_module(self) -> str:
        """生成依赖注入模块代码（Koin 示例）"""
        lines = [
            f"package {self.base_package}.config",
            "",
            "import okhttp3.OkHttpClient",
            "import org.koin.dsl.module",
            "import retrofit2.Retrofit",
            f"import {self.base_package}.services.ApiService",
            "",
            "/**",
            " * 网络模块依赖注入配置",
            " * 使用 Koin 进行依赖注入",
            " */",
            "val networkModule = module {",
            "    single { OkHttpConfig.createOkHttpClient() }",
            "    single { OkHttpConfig.createRetrofit() }",
            "    single { get<Retrofit>().create(ApiService::class.java) }",
            "}",
        ]
        
        return "\n".join(lines)

