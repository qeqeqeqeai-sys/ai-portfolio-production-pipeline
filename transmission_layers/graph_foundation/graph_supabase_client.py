import os,time,requests
from typing import *

class SupabaseRestClient:
    def __init__(self):
        self.url=os.getenv("SUPABASE_URL")
        self.key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.base_url=self.url.rstrip("/")+"/rest/v1"
        self.headers={"apikey":self.key,"Authorization":f"Bearer {self.key}","Content-Type":"application/json"}

    def _request(self,method,path,params=None,json_body=None,prefer=None):
        headers=dict(self.headers)
        if prefer:
            headers["Prefer"]=prefer
        url=f"{self.base_url}/{path}"
        last=None
        for i in range(3):
            try:
                r=requests.request(method,url,headers=headers,params=params,json=json_body,timeout=60)
                if r.status_code in (200,201,204):
                    return r.json() if r.text else []
                last=f"{r.status_code}: {r.text}"
            except Exception as e:
                last=str(e)
            time.sleep(i+1)
        raise RuntimeError(last)

    def select(self,table,columns="*",filters=None,order=None,limit=None):
        params={"select":columns}
        if filters: params.update(filters)
        if order: params["order"]=order
        if limit is not None: params["limit"]=str(limit)
        return self._request("GET",table,params=params)

    def insert(self,table,rows,return_rows=False):
        return self._request("POST",table,json_body=rows,
            prefer="return=representation" if return_rows else "return=minimal")

    def upsert(self,table,rows,on_conflict,return_rows=False):
        return self._request("POST",table,params={"on_conflict":on_conflict},
            json_body=rows,
            prefer="resolution=merge-duplicates,"+("return=representation" if return_rows else "return=minimal"))
