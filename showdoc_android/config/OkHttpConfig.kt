package com.cqfengli.api.config

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import com.cqfengli.api.services.ApiService

/**
 * OkHttp 和 Retrofit 配置
 * 自动生成的配置文件
 * 由 ShowDoc 文档自动生成
 */
object OkHttpConfig {

    private const val BASE_URL = "https://api.example.com"
    private const val TIMEOUT_SECONDS = 30L

    /**
     * 创建 OkHttpClient
     */
    fun createOkHttpClient(): OkHttpClient {
        val builder = OkHttpClient.Builder()

        // 设置超时时间
        builder.connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        builder.readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        builder.writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)

        // 添加日志拦截器（仅在 Debug 模式下）
        if (BuildConfig.DEBUG) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            builder.addInterceptor(loggingInterceptor)
        }

        // TODO: 根据需要添加其他拦截器
        // 例如：认证拦截器、错误处理拦截器等

        return builder.build()
    }

    /**
     * 创建 Retrofit 实例
     */
    fun createRetrofit(): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(createOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    /**
     * 创建 ApiService 实例
     */
    fun createApiService(): ApiService {
        return createRetrofit().create(ApiService::class.java)
    }

}