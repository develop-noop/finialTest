using UnityEngine;
using UnityEngine.UI;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System;

public class UDPReceive : MonoBehaviour
{
    Thread receiveThread;
    UdpClient client;
    public int port = 5065;

    public Animator anim;
    public RawImage camScreen;
    
    private Texture2D tex;
    private string receivedString = "";
    private bool hasNewData = false;
    private object dataLock = new object();

    // 쓰다듬기 거리 설정 (인식이 잘 안 되면 숫자를 200~300으로 늘리세요)
    public float petDistance = 150f; 

    void Start()
    {
        anim = GetComponent<Animator>();
        tex = new Texture2D(320, 240, TextureFormat.RGB24, false);
        if (camScreen != null) camScreen.texture = tex;

        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveData()
    {
        client = new UdpClient(port);
        while (true)
        {
            try
            {
                IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
                byte[] data = client.Receive(ref anyIP);
                lock (dataLock)
                {
                    receivedString = Encoding.UTF8.GetString(data);
                    hasNewData = true;
                }
            }
            catch { }
        }
    }

    void Update()
    {
        if (hasNewData)
        {
            string currentData = "";
            lock (dataLock)
            {
                currentData = receivedString;
                hasNewData = false;
            }

            string[] splitData = currentData.Split('|');

            // 1. 행동 로직 (파이썬 신호 처리)
            if (splitData.Length > 0)
            {
                string[] info = splitData[0].Split(',');
                string command = info[0];
                
                float fingerX = 0;
                float fingerY = 0;
                if(info.Length >= 3) {
                     fingerX = float.Parse(info[1]);
                     fingerY = float.Parse(info[2]);
                }

                // --- 동작 결정 ---
                if (command == "fist") 
                { 
                    anim.Play("GoatSheep_Attack01"); 
                }
                else if (command == "palm") 
                { 
                    // ★ 여기가 핵심! 손 펴면 무조건 즉시 Idle!
                    anim.Play("Idle"); 
                }
                else if (command == "pet")
                {
                    // 검지 하나일 때만 거리 계산
                    CheckPetting(fingerX, fingerY);
                }
            }

            // 2. 배경 그리기 (중복 없이 한 번만!)
            if (splitData.Length > 1 && camScreen != null)
            {
                try
                {
                    byte[] imageBytes = Convert.FromBase64String(splitData[1]);
                    tex.LoadImage(imageBytes);
                }
                catch { }
            }
        }
    }

    // ★ 쓰다듬기 판독 함수
    void CheckPetting(float x, float y)
    {
        // 양의 머리 위치 (화면 좌표)
        Vector3 sheepScreenPos = Camera.main.WorldToScreenPoint(transform.position + Vector3.up * 1.5f);
        
        // 내 손가락 위치
        Vector2 fingerScreenPos = new Vector2(x * Screen.width, y * Screen.height);

        // 거리 계산
        float dist = Vector2.Distance(fingerScreenPos, sheepScreenPos);

        if (dist < petDistance)
        {
            // 거리 가까우면 쓰다듬기 (Eating)
            anim.Play("GoatSheep_Eating"); 
        }
        else
        {
            // ★ 거리 멀어지면 바로 Idle (여기도 중요!)
            anim.Play("Idle"); 
        }
    }

    void OnApplicationQuit()
    {
        if (receiveThread != null) receiveThread.Abort();
        if (client != null) client.Close();
    }
}