#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import json
import sys
from unittest.mock import patch, MagicMock

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from utils.cipher import CustomCipher, DecryptError


class TestCustomCipher(unittest.TestCase):

    def setUp(self):
        """测试前设置"""
        self.cipher = CustomCipher()

    def test_generate_random_string_default(self):
        """测试生成默认长度的随机字符串"""
        result = self.cipher.generate_random_string()
        self.assertEqual(len(result), 16)
        # 检查字符串只包含字母和数字
        self.assertTrue(all(c.isalnum() for c in result))

    def test_generate_random_string_custom_length(self):
        """测试生成自定义长度的随机字符串"""
        result = self.cipher.generate_random_string(length=32)
        self.assertEqual(len(result), 32)

    def test_generate_random_string_custom_seed(self):
        """测试使用自定义字符集生成随机字符串"""
        seed = "ABC123"
        result = self.cipher.generate_random_string(length=10, seed=seed)
        self.assertEqual(len(result), 10)
        # 检查字符串只包含自定义字符集中的字符
        self.assertTrue(all(c in seed for c in result))

    @patch.dict(os.environ, {'CIPHER_HALF_KEY_2': 'test_half_key_2'})
    def test_generate_root_key_with_env(self):
        """测试使用环境变量生成根密钥"""
        half_key_1 = "test_half_key_1"
        result = CustomCipher._generate_root_key(half_key_1)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # 32字节 = 64十六进制字符，但切片后为32字节

    def test_generate_root_key_without_env(self):
        """测试使用默认值生成根密钥"""
        # 确保环境变量不存在
        if 'CIPHER_HALF_KEY_2' in os.environ:
            del os.environ['CIPHER_HALF_KEY_2']
        
        half_key_1 = "test_half_key_1"
        result = CustomCipher._generate_root_key(half_key_1)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)

    def test_encrypt_decrypt_roundtrip_string(self):
        """测试字符串加密解密的往返正确性"""
        plaintext = "这是一个测试字符串"
        
        # 加密
        ciphertext_data = self.cipher.encrypt_plaintext(plaintext)
        
        # 验证加密结果结构
        self.assertIn('half_key', ciphertext_data)
        self.assertIn('encrypted_work_key', ciphertext_data)
        self.assertIn('work_key_iv', ciphertext_data)
        self.assertIn('plaintext_iv', ciphertext_data)
        self.assertIn('ciphertext', ciphertext_data)
        
        # 解密
        decrypted = self.cipher.decrypt_ciphertext_data(ciphertext_data)
        
        # 验证解密结果
        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_roundtrip_dict(self):
        """测试字典加密解密的往返正确性"""
        plaintext = {
            "name": "测试",
            "value": 123,
            "nested": {
                "key": "value"
            }
        }
        
        # 加密
        ciphertext_data = self.cipher.encrypt_plaintext(plaintext)
        
        # 解密
        decrypted = self.cipher.decrypt_ciphertext_data(ciphertext_data)
        
        # 验证解密结果
        self.assertEqual(decrypted, plaintext)

    def test_decrypt_invalid_ciphertext_missing_field(self):
        """测试解密缺少字段的密文"""
        ciphertext_data = {
            'half_key': 'test',
            'encrypted_work_key': 'test',
            'work_key_iv': 'test',
            'plaintext_iv': 'test',
            # 缺少 'ciphertext' 字段
        }
        
        with self.assertRaises(DecryptError) as context:
            self.cipher.decrypt_ciphertext_data(ciphertext_data)
        
        self.assertIn('Failed to decrypt', str(context.exception))

    def test_decrypt_invalid_ciphertext_empty_field(self):
        """测试解密有空字段的密文"""
        ciphertext_data = {
            'half_key': '',
            'encrypted_work_key': 'test',
            'work_key_iv': 'test',
            'plaintext_iv': 'test',
            'ciphertext': 'test'
        }
        
        with self.assertRaises(DecryptError) as context:
            self.cipher.decrypt_ciphertext_data(ciphertext_data)
        
        self.assertIn('Failed to decrypt', str(context.exception))

    def test_decrypt_invalid_base64(self):
        """测试解密无效的Base64编码"""
        ciphertext_data = {
            'half_key': 'test',
            'encrypted_work_key': 'not-valid-base64!',
            'work_key_iv': 'test',
            'plaintext_iv': 'test',
            'ciphertext': 'test'
        }
        
        # 这里应该会抛出binascii.Error或类似异常
        with self.assertRaises(Exception):
            self.cipher.decrypt_ciphertext_data(ciphertext_data)

    def test_encrypt_different_inputs_produce_different_outputs(self):
        """测试相同明文多次加密产生不同的输出（由于随机IV）"""
        plaintext = "相同的明文"
        
        # 第一次加密
        ciphertext_data1 = self.cipher.encrypt_plaintext(plaintext)
        
        # 第二次加密
        ciphertext_data2 = self.cipher.encrypt_plaintext(plaintext)
        
        # 验证两次加密的结果不同（由于随机IV和half_key）
        self.assertNotEqual(ciphertext_data1['ciphertext'], ciphertext_data2['ciphertext'])
        self.assertNotEqual(ciphertext_data1['half_key'], ciphertext_data2['half_key'])

    def test_decrypt_error_class(self):
        """测试DecryptError异常类"""
        error_message = "测试错误消息"
        error = DecryptError(error_message)
        
        self.assertEqual(str(error), error_message)
        self.assertIsInstance(error, Exception)

    @patch('utils.cipher.secrets.token_bytes')
    def test_generate_work_key(self, mock_token_bytes):
        """测试工作密钥生成"""
        # 模拟secrets.token_bytes返回固定值
        mock_token_bytes.side_effect = [
            b'work_key_32_bytes_123456789012',  # work_key
            b'work_key_iv_16_bytes'            # work_key_iv
        ]
        
        half_key = "test_half_key"
        encrypted_work_key, work_key_iv, work_key = self.cipher._generate_work_key(half_key)
        
        # 验证返回类型
        self.assertIsInstance(encrypted_work_key, str)
        self.assertIsInstance(work_key_iv, str)
        self.assertIsInstance(work_key, bytes)
        
        # 验证Base64编码
        import base64
        try:
            base64.b64decode(encrypted_work_key)
            base64.b64decode(work_key_iv)
        except Exception:
            self.fail("返回的字符串不是有效的Base64编码")

    @patch('utils.cipher.b64decode')
    @patch('utils.cipher.CustomCipher._generate_root_key')
    @patch('utils.cipher.CustomCipher._decrypt')
    def test_decrypt_work_key(self, mock_decrypt, mock_generate_root_key, mock_b64decode):
        """测试工作密钥解密"""
        # 设置模拟
        mock_generate_root_key.return_value = b'root_key_32_bytes'
        mock_b64decode.side_effect = [
            b'encrypted_work_key_bytes',
            b'work_key_iv_bytes'
        ]
        mock_decrypt.return_value = b'decrypted_work_key'
        
        half_key = "test_half_key"
        encrypted_work_key = "encrypted_work_key_base64"
        work_key_iv = "work_key_iv_base64"
        
        result = self.cipher._decrypt_work_key(half_key, encrypted_work_key, work_key_iv)
        
        # 验证调用
        mock_generate_root_key.assert_called_once_with(half_key)
        self.assertEqual(mock_b64decode.call_count, 2)
        mock_decrypt.assert_called_once_with(
            b'root_key_32_bytes',
            b'work_key_iv_bytes',
            b'encrypted_work_key_bytes'
        )
        
        # 验证结果
        self.assertEqual(result, b'decrypted_work_key')

    def test_encrypt_plaintext_handles_json_serialization(self):
        """测试encrypt_plaintext正确处理JSON序列化"""
        # 测试非字符串/字典类型应该被JSON序列化
        test_cases = [
            "字符串",
            {"key": "value"},
            ["列表", 123],
            123,  # 数字
            True,  # 布尔值
            None  # null
        ]
        
        for plaintext in test_cases:
            try:
                ciphertext_data = self.cipher.encrypt_plaintext(plaintext)
                decrypted = self.cipher.decrypt_ciphertext_data(ciphertext_data)
                
                # 验证解密后的值与原始值相等（经过JSON序列化/反序列化）
                self.assertEqual(decrypted, plaintext)
            except Exception as e:
                self.fail(f"加密解密失败，输入: {plaintext}, 错误: {e}")


if __name__ == '__main__':
    unittest.main()

