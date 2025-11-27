package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 检查试用次数(104) (CheckNumBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4480
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "free": 1,
 *     "num": 1
 *   },
 *   "hasNext": 0
 * }
 */
@Parcelize
data class CheckNumBean(
    var free: Int,
    var num: Int
) : Parcelable