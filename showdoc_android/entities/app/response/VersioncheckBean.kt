package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

/**
 * 版本检测 (VersioncheckBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4460
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "description": "因您当前版本过低，为保证您能正常使用，请先下载更新版本",
 *     "updateUrl": "https://apps.apple.com/cn/app/%E5%AE%9A%E5%88%B6%E6%B0%B4%E5%8D%B0%E7%9B%B8%E6%9C%BA-%E6%97%B6%E9%97%B4%E5%9C%B0%E7%82%B9%E5%B7%A5%E4%BD%9C%E6%B0%B4%E5%8D%B0/id1581095450",
 *     "forceUpdate": "1",
 *     "isUpdate": "1"
 *   }
 * }
 */
@Parcelize
data class VersioncheckBean(
    var description: String,
    var updateUrl: String,
    var forceUpdate: String,
    var isUpdate: String
) : Parcelable