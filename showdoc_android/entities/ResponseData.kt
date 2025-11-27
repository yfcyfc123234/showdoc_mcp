package com.cqfengli.api.entities

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 通用响应数据包装类
 * 所有 API 响应都使用此包装格式
 * 自动生成的实体类
 * 由 ShowDoc 文档自动生成
 */
@Parcelize
data class ResponseData<out T : Parcelable>(
    var code: Int,

    var msg: String,

    val data: T,

    var hasNext: Int,
) : Parcelable {
    companion object {
        const val REQUEST_CODE_SUCCESS = 1
    }

    val success: Boolean
        get() = code == REQUEST_CODE_SUCCESS
}