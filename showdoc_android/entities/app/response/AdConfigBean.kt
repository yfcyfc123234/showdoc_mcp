package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 广告配置 (AdConfigBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4482
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "APPID": "5627622",
 *     "KP": "961774351",
 *     "NEW_CP": "890267166"
 *   },
 *   "hasNext": 0
 * }
 */
@Parcelize
data class AdConfigBean(
    var APPID: String,
    var KP: String,
    var NEW_CP: String
) : Parcelable