/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-08-09
 * =================================================================================================================== */

// 如果没有 icon 图片，生成背景色
export function generateIconBgColor(inputString: string): string {
  let hash = 0;
  for (let i = 0; i < inputString.length; i++) {
    hash = ((hash << 5) - hash) + inputString.charCodeAt(i);
    hash |= 0;
  }
  hash = Math.abs(hash);
  const r = (hash % 160) + 60;
  const g = ((hash >> 8) % 160) + 60;
  const b = (((hash >> 16) ^ inputString.length) % 160) + 60;
  return `rgb(${r}, ${g}, ${b})`;
}