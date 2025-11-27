package com.cqfengli.api.services

import retrofit2.http.*
import retrofit2.Call
import retrofit2.Response
import okhttp3.FormBody
import com.cqfengli.api.entities.ResponseData
import com.cqfengli.api.entities.app.request.*
import com.cqfengli.api.entities.app.response.*

/**
 * 自动生成的 Retrofit Service 接口
 * 由 ShowDoc 文档自动生成
 * 所有响应都使用 ResponseData<T> 包装格式
 */
interface ApiService {

    /**
     * 应用授权
     * App授权接口
     * 来源: 应用授权
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/get_auth?grantType=user_credential
     */
    @GET("/api/v1/get_auth")
    suspend fun getAuth(
    ): Response<ResponseData<GetAuthBean>>

    /**
     * 应用配置
     * 应用配置接口
     * 来源: 应用配置
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/config
     */
    @GET("/api/v1/config")
    suspend fun config(
    ): Response<ResponseData<V1ConfigBean>>

    /**
     * 教程页面
     * 来源: 教程页面
     * 分类: 应用
     * API: GET {{baseurl}}/v2/jc
     */
    @GET("/v2/jc")
    suspend fun jc(
    ): Response<ResponseData<Any>>

    /**
     * 苹果广告
     * 来源: 苹果广告
     * 分类: 应用
     * API: POST {{baseurl}}/v2/iad
     */
    @POST("/v2/iad")
    suspend fun iad(
    ): Response<ResponseData<Any>>

    /**
     * 版本检测
     * 版本检测
     * 来源: 版本检测
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/versionCheck
     */
    @GET("/api/v1/versionCheck")
    suspend fun versioncheck(
    ): Response<ResponseData<VersioncheckBean>>

    /**
     * 获取首页banner及功能区配置
     * 获取首页banner及功能区配置
     * 来源: 获取首页banner及功能区配置
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/homelist
     */
    @GET("/api/v1/homelist")
    suspend fun homelist(
    ): Response<ResponseData<HomelistBean>>

    /**
     * 开屏付费配置
     * 开屏付费配置
     * 来源: 开屏付费配置
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/open/conf
     */
    @GET("/api/v1/open/conf")
    suspend fun conf(
    ): Response<ResponseData<ConfBean>>

    /**
     * 图片验证码，验证码中含字母和数字
     * 来源: 图片验证码
     * 分类: 应用
     * API: GET {{baseurl}}/v2/captcha?token=7b7808bb0a5e2a877870&type=cdk
     */
    @GET("/v2/captcha")
    suspend fun captcha(
    ): Response<ResponseData<CaptchaBean>>

    /**
     * 检查试用次数(104)
     * 检查试用次数
     * 来源: 检查试用次数(104)
     * 分类: 应用
     * API: POST {{baseurl}}/api/v1/check_num
     */
    @POST("/api/v1/check_num")
    suspend fun checkNum(
    ): Response<ResponseData<CheckNumBean>>

    /**
     * 扣除试用次数(104)
     * 扣除试用次数
     * 来源: 扣除试用次数(104)
     * 分类: 应用
     * API: POST {{baseurl}}/api/v1/deduct_num
     */
    @POST("/api/v1/deduct_num")
    suspend fun deductNum(
    ): Response<ResponseData<Any>>

    /**
     * 广告配置
     * 广告配置
     * 来源: 广告配置
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/ad/config
     */
    @GET("/api/v1/ad/config")
    suspend fun config(
    ): Response<ResponseData<AdConfigBean>>

    /**
     * 弹窗广告控制
     * 弹窗广告控制
     * 来源: 弹窗广告控制
     * 分类: 应用
     * API: GET {{baseurl}}/api/v1/ad_ctr
     */
    @GET("/api/v1/ad_ctr")
    suspend fun adCtr(
    ): Response<ResponseData<AdCtrBean>>

}