using UnityEngine;
using UnityEngine.UI; // 이미지를 다루기 위해 추가
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System;

public class UDPReceive : MonoBehaviour
{
    Thread receiveThread;
    UdpClient client;
    public int port = 5052;

    public RawImage camScreen; // 배경화면 연결할 변수
    private Texture2D tex;
    
    // 받은 데이터를 메인 스레드로 옮기기 위한 변수들
    private string receivedString = "";
    private bool hasNewData = false;
    private object dataLock = new object();

    public Vector3 targetPosition;

    void Start()
    {
        // 빈 도화지 생성
        tex = new Texture2D(320, 240, TextureFormat.RGB24, false);
        if(camScreen != null) camScreen.texture = tex;

        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    private void ReceiveData()
    {
        client = new UdpClient(port);
        while (true)
        {
            try
            {
                IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
                byte[] data = client.Receive(ref anyIP);
                
                // 데이터를 받아서 임시 저장 (Lock 사용)
                lock(dataLock) 
                {
                    receivedString = Encoding.UTF8.GetString(data);
                    hasNewData = true;
                }
            }
            catch (Exception err)
            {
                // 에러 무시
            }
        }
    }

    void Update()
    {
        // 메인 스레드에서만 화면 갱신이 가능함
        if (hasNewData)
        {
            string currentData = "";
            lock(dataLock)
            {
                currentData = receivedString;
                hasNewData = false;
            }

            // 데이터 분해: "좌표|이미지"
            string[] splitData = currentData.Split('|');
            
            // 1. 좌표 처리
            if (splitData.Length > 0)
            {
                string[] points = splitData[0].Split(',');
                if (points.Length >= 2)
                {
                    float x = float.Parse(points[0]) * 10 - 5;
                    float y = float.Parse(points[1]) * 10 - 5;
                    targetPosition = new Vector3(x, -y, 0);
                }
            }

            // 2. 이미지 처리
            if (splitData.Length > 1 && camScreen != null)
            {
                try
                {
                    byte[] imageBytes = Convert.FromBase64String(splitData[1]);
                    tex.LoadImage(imageBytes); // 이미지 로드
                }
                catch {}
            }
        }

        // 공 이동
        transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * 10);
    }
    
    void OnApplicationQuit()
    {
        if (receiveThread != null) receiveThread.Abort();
        client.Close();
    }
}