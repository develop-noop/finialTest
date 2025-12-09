using System.Net.Sockets;
using System.Text;
using UnityEngine;

public class STTModeSender : MonoBehaviour
{
    public string pythonIP = "127.0.0.1";
    public int pythonPort = 6000;

    private int currentMode = 0;

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Keypad2))
        {
            SendCommand("MODE_WHISPER_SIMPLE");
            currentMode = 2;
            Debug.Log("현재 음성인식 모드: 2 (Whisper 기본 QA)");
        }
        else if (Input.GetKeyDown(KeyCode.Keypad3))
        {
            SendCommand("MODE_WHISPER_PERSONA");
            currentMode = 3;
            Debug.Log("현재 음성인식 모드: 3 (Whisper 성격 LLM QA)");
        }
    }

    void SendCommand(string cmd)
    {
        try
        {
            using (UdpClient client = new UdpClient())
            {
                byte[] data = Encoding.UTF8.GetBytes(cmd);
                client.Send(data, data.Length, pythonIP, pythonPort);
            }
            Debug.Log("Python으로 전송: " + cmd);
        }
        catch (System.Exception e)
        {
            Debug.LogWarning("명령 전송 실패: " + e.Message);
        }
    }
}
