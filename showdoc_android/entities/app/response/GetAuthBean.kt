package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 应用授权 (GetAuthBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4454
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "access_token": "013be7ab0671f7328ed875432a736a16",
 *     "active_time": 1658821419
 *   }
 * }
 */
@Parcelize
data class GetAuthBean(
    var access_token: String,
    var active_time: Int
) : Parcelable