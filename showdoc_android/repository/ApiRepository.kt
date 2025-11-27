package com.cqfengli.api.repository

import com.cqfengli.api.entities.ResponseData
import com.cqfengli.api.services.ApiService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Response
import com.cqfengli.api.entities.app.request.*
import com.cqfengli.api.entities.app.response.*

/**
 * 自动生成的 Repository 类
 * 由 ShowDoc 文档自动生成
 * 所有响应都使用 ResponseData<T> 包装格式
 */
open class ApiRepository(
    private val apiService: ApiService
) {

    /**
     * 通用请求方法
     * 处理响应并提取 ResponseData
     */
    private suspend fun <T> request(
        call: suspend () -> Response<ResponseData<T>>
    ): ResponseData<T> {
        return withContext(Dispatchers.IO) {
            val response = call.invoke()
            if (response.isSuccessful && response.body() != null) {
                response.body()!!
            } else {
                // 处理错误响应
                ResponseData(
                    code = response.code(),
                    msg = response.message() ?: "请求失败",
                    data = null as T,
                    hasNext = 0
                )
            }
        }.apply {
            // 处理登录过期等业务逻辑
            if (code == 201 || code == 202) {
                // 登录过期，可以在这里处理
            }
        }
    }

    companion object {
        @Volatile
        private var INSTANCE: ApiRepository? = null

        fun getInstance(apiService: ApiService): ApiRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: ApiRepository(apiService).also { INSTANCE = it }
            }
        }
    }

    /**
     * 应用授权
     * App授权接口
     * 来源: 应用授权
     */
    suspend fun getAuth(): ResponseData<GetAuthBean> = request {
        apiService.getAuth()
    }

    /**
     * 应用配置
     * 应用配置接口
     * 来源: 应用配置
     */
    suspend fun config(): ResponseData<Any> = request {
        apiService.config()
    }

    /**
     * 教程页面
     * 来源: 教程页面
     */
    suspend fun jc(): ResponseData<Any> = request {
        apiService.jc()
    }

    /**
     * 苹果广告
     * 来源: 苹果广告
     */
    suspend fun iad(): ResponseData<Any> = request {
        apiService.iad()
    }

    /**
     * 版本检测
     * 版本检测
     * 来源: 版本检测
     */
    suspend fun versioncheck(): ResponseData<VersioncheckBean> = request {
        apiService.versioncheck()
    }

    /**
     * 获取首页banner及功能区配置
     * 获取首页banner及功能区配置
     * 来源: 获取首页banner及功能区配置
     */
    suspend fun homelist(): ResponseData<HomelistBean> = request {
        apiService.homelist()
    }

    /**
     * 开屏付费配置
     * 开屏付费配置
     * 来源: 开屏付费配置
     */
    suspend fun conf(): ResponseData<ConfBean> = request {
        apiService.conf()
    }

    /**
     * 图片验证码，验证码中含字母和数字
     * 来源: 图片验证码
     */
    suspend fun captcha(): ResponseData<CaptchaBean> = request {
        apiService.captcha()
    }

    /**
     * 检查试用次数(104)
     * 检查试用次数
     * 来源: 检查试用次数(104)
     */
    suspend fun checkNum(): ResponseData<CheckNumBean> = request {
        apiService.checkNum()
    }

    /**
     * 扣除试用次数(104)
     * 扣除试用次数
     * 来源: 扣除试用次数(104)
     */
    suspend fun deductNum(): ResponseData<Any> = request {
        apiService.deductNum()
    }

    /**
     * 广告配置
     * 广告配置
     * 来源: 广告配置
     */
    suspend fun config(): ResponseData<Any> = request {
        apiService.config()
    }

    /**
     * 弹窗广告控制
     * 弹窗广告控制
     * 来源: 弹窗广告控制
     */
    suspend fun adCtr(): ResponseData<AdCtrBean> = request {
        apiService.adCtr()
    }

}